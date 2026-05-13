from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_department_service, get_employee_service
from app.main import app
from app.services.department import DepartmentService
from app.services.employee import EmployeeService


@pytest.fixture
def client(sqlite_session_factory):
    async def override_get_department_service():
        async with sqlite_session_factory() as session:
            yield DepartmentService(session)

    async def override_get_employee_service():
        async with sqlite_session_factory() as session:
            yield EmployeeService(session)

    app.dependency_overrides[get_department_service] = override_get_department_service
    app.dependency_overrides[get_employee_service] = override_get_employee_service

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def test_create_department_and_child_department(client: TestClient) -> None:
    root_response = client.post("/departments/", json={"name": "  Operations  "})

    assert root_response.status_code == 201
    root_payload = root_response.json()
    assert root_payload["name"] == "Operations"
    assert root_payload["parent_id"] is None
    assert root_payload["id"] > 0
    assert "created_at" in root_payload

    child_response = client.post(
        "/departments/",
        json={"name": "Payroll", "parent_id": root_payload["id"]},
    )

    assert child_response.status_code == 201
    child_payload = child_response.json()
    assert child_payload["name"] == "Payroll"
    assert child_payload["parent_id"] == root_payload["id"]
    assert child_payload["id"] > root_payload["id"]


def test_create_department_rejects_duplicate_name_within_same_parent(client: TestClient) -> None:
    root_response = client.post("/departments/", json={"name": "Operations"})
    root_id = root_response.json()["id"]

    first_response = client.post(
        "/departments/",
        json={"name": "  Backend  ", "parent_id": root_id},
    )

    assert first_response.status_code == 201
    assert first_response.json()["name"] == "Backend"

    response = client.post(
        "/departments/",
        json={"name": "Backend", "parent_id": root_id},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Department with this name already exists in this parent",
    }


def test_create_department_with_missing_parent_returns_404(client: TestClient) -> None:
    response = client.post(
        "/departments/",
        json={"name": "Payroll", "parent_id": 999},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Parent department not found"}


def test_create_employee_for_department(client: TestClient) -> None:
    department_response = client.post("/departments/", json={"name": "Operations"})
    department_id = department_response.json()["id"]

    response = client.post(
        f"/departments/{department_id}/employees/",
        json={
            "full_name": "Ada Lovelace",
            "position": "Analyst",
            "hired_at": "2026-05-01",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    employee = payload["employee"]
    assert employee["department_id"] == department_id
    assert employee["full_name"] == "Ada Lovelace"
    assert employee["position"] == "Analyst"
    assert employee["hired_at"] == "2026-05-01"
    assert employee["id"] > 0
    assert "created_at" in employee


def test_create_employee_for_missing_department_returns_404(client: TestClient) -> None:
    response = client.post(
        "/departments/999/employees/",
        json={
            "full_name": "Ada Lovelace",
            "position": "Analyst",
            "hired_at": None,
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Department not found"}


def test_get_department_details_with_subtree_and_employees(client: TestClient) -> None:
    root_response = client.post("/departments/", json={"name": "Operations"})
    root_id = root_response.json()["id"]

    child_response = client.post(
        "/departments/",
        json={"name": "Payroll", "parent_id": root_id},
    )
    child_id = child_response.json()["id"]

    grandchild_response = client.post(
        "/departments/",
        json={"name": "Support", "parent_id": child_id},
    )
    grandchild_id = grandchild_response.json()["id"]

    client.post(
        f"/departments/{root_id}/employees/",
        json={
            "full_name": "Alice Root",
            "position": "Head",
            "hired_at": "2026-05-01",
        },
    )
    client.post(
        f"/departments/{child_id}/employees/",
        json={
            "full_name": "Bob Child",
            "position": "Analyst",
            "hired_at": "2026-05-02",
        },
    )
    client.post(
        f"/departments/{grandchild_id}/employees/",
        json={
            "full_name": "Cara Grandchild",
            "position": "Specialist",
            "hired_at": "2026-05-03",
        },
    )

    response = client.get(f"/departments/{root_id}?depth=2&include_employees=true")

    assert response.status_code == 200
    payload = response.json()
    assert payload["department"]["id"] == root_id
    assert [employee["full_name"] for employee in payload["employees"]] == ["Alice Root"]
    assert len(payload["children"]) == 1

    child_payload = payload["children"][0]
    assert child_payload["department"]["id"] == child_id
    assert [employee["full_name"] for employee in child_payload["employees"]] == ["Bob Child"]
    assert len(child_payload["children"]) == 1

    grandchild_payload = child_payload["children"][0]
    assert grandchild_payload["department"]["id"] == grandchild_id
    assert [employee["full_name"] for employee in grandchild_payload["employees"]] == ["Cara Grandchild"]
    assert grandchild_payload["children"] == []


def test_get_department_details_without_employees(client: TestClient) -> None:
    root_response = client.post("/departments/", json={"name": "Operations"})
    root_id = root_response.json()["id"]

    response = client.get(f"/departments/{root_id}?include_employees=false")

    assert response.status_code == 200
    payload = response.json()
    assert payload["department"]["id"] == root_id
    assert payload["employees"] == []
    assert payload["children"] == []


def test_get_department_details_returns_404_for_missing_department(client: TestClient) -> None:
    response = client.get("/departments/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Department not found"}


def test_update_department_moves_it_to_another_parent_and_renames(client: TestClient) -> None:
    root_response = client.post("/departments/", json={"name": "Operations"})
    root_id = root_response.json()["id"]

    new_parent_response = client.post("/departments/", json={"name": "Corporate"})
    new_parent_id = new_parent_response.json()["id"]

    child_response = client.post(
        "/departments/",
        json={"name": "Payroll", "parent_id": root_id},
    )
    child_id = child_response.json()["id"]

    response = client.patch(
        f"/departments/{child_id}",
        json={"name": "Payroll & Benefits", "parent_id": new_parent_id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == child_id
    assert payload["name"] == "Payroll & Benefits"
    assert payload["parent_id"] == new_parent_id

    subtree_response = client.get(f"/departments/{new_parent_id}?depth=1")
    subtree_payload = subtree_response.json()
    assert [child["department"]["id"] for child in subtree_payload["children"]] == [child_id]


def test_update_department_rejects_duplicate_name_within_same_parent(client: TestClient) -> None:
    root_response = client.post("/departments/", json={"name": "Operations"})
    root_id = root_response.json()["id"]

    first_child_response = client.post(
        "/departments/",
        json={"name": "Backend", "parent_id": root_id},
    )
    first_child_id = first_child_response.json()["id"]

    second_child_response = client.post(
        "/departments/",
        json={"name": "Platform", "parent_id": root_id},
    )
    second_child_id = second_child_response.json()["id"]

    response = client.patch(
        f"/departments/{second_child_id}",
        json={"name": "Backend"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Department with this name already exists in this parent",
    }

    assert client.get(f"/departments/{first_child_id}").status_code == 200
    assert client.get(f"/departments/{second_child_id}").status_code == 200


def test_update_department_can_detach_from_parent(client: TestClient) -> None:
    root_response = client.post("/departments/", json={"name": "Operations"})
    root_id = root_response.json()["id"]

    child_response = client.post(
        "/departments/",
        json={"name": "Payroll", "parent_id": root_id},
    )
    child_id = child_response.json()["id"]

    response = client.patch(
        f"/departments/{child_id}",
        json={"parent_id": None},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == child_id
    assert payload["parent_id"] is None

    root_children_response = client.get(f"/departments/{root_id}?depth=1")
    assert root_children_response.json()["children"] == []


def test_update_department_rejects_self_parent(client: TestClient) -> None:
    department_response = client.post("/departments/", json={"name": "Operations"})
    department_id = department_response.json()["id"]

    response = client.patch(
        f"/departments/{department_id}",
        json={"parent_id": department_id},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Department cannot be its own parent"}


def test_update_department_rejects_moving_into_own_subtree(client: TestClient) -> None:
    root_response = client.post("/departments/", json={"name": "Operations"})
    root_id = root_response.json()["id"]

    child_response = client.post(
        "/departments/",
        json={"name": "Payroll", "parent_id": root_id},
    )
    child_id = child_response.json()["id"]

    grandchild_response = client.post(
        "/departments/",
        json={"name": "Support", "parent_id": child_id},
    )
    grandchild_id = grandchild_response.json()["id"]

    response = client.patch(
        f"/departments/{root_id}",
        json={"parent_id": grandchild_id},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Department cannot be moved into its own subtree"}


def test_delete_department_cascade_removes_tree_and_employees(client: TestClient) -> None:
    root_response = client.post("/departments/", json={"name": "Operations"})
    root_id = root_response.json()["id"]

    child_response = client.post(
        "/departments/",
        json={"name": "Payroll", "parent_id": root_id},
    )
    child_id = child_response.json()["id"]

    grandchild_response = client.post(
        "/departments/",
        json={"name": "Support", "parent_id": child_id},
    )
    grandchild_id = grandchild_response.json()["id"]

    client.post(
        f"/departments/{root_id}/employees/",
        json={
            "full_name": "Alice Root",
            "position": "Head",
            "hired_at": "2026-05-01",
        },
    )
    client.post(
        f"/departments/{child_id}/employees/",
        json={
            "full_name": "Bob Child",
            "position": "Analyst",
            "hired_at": "2026-05-02",
        },
    )

    response = client.delete(f"/departments/{root_id}?mode=cascade")

    assert response.status_code == 204
    assert client.get(f"/departments/{root_id}").status_code == 404
    assert client.get(f"/departments/{child_id}").status_code == 404
    assert client.get(f"/departments/{grandchild_id}").status_code == 404


def test_delete_department_reassign_moves_employees_and_promotes_children(client: TestClient) -> None:
    root_response = client.post("/departments/", json={"name": "Operations"})
    root_id = root_response.json()["id"]

    target_response = client.post("/departments/", json={"name": "Finance"})
    target_id = target_response.json()["id"]

    child_response = client.post(
        "/departments/",
        json={"name": "Payroll", "parent_id": root_id},
    )
    child_id = child_response.json()["id"]

    grandchild_response = client.post(
        "/departments/",
        json={"name": "Support", "parent_id": child_id},
    )
    grandchild_id = grandchild_response.json()["id"]

    client.post(
        f"/departments/{child_id}/employees/",
        json={
            "full_name": "Bob Child",
            "position": "Analyst",
            "hired_at": "2026-05-02",
        },
    )

    response = client.delete(
        f"/departments/{child_id}?mode=reassign&reassign_to_department_id={target_id}"
    )

    assert response.status_code == 204

    target_payload = client.get(f"/departments/{target_id}?depth=1").json()
    assert [employee["full_name"] for employee in target_payload["employees"]] == ["Bob Child"]

    root_payload = client.get(f"/departments/{root_id}?depth=1").json()
    assert [child["department"]["id"] for child in root_payload["children"]] == [grandchild_id]
    assert root_payload["children"][0]["department"]["parent_id"] == root_id


def test_delete_department_requires_reassign_target_when_mode_is_reassign(client: TestClient) -> None:
    department_response = client.post("/departments/", json={"name": "Operations"})
    department_id = department_response.json()["id"]

    response = client.delete(f"/departments/{department_id}?mode=reassign")

    assert response.status_code == 400
    assert response.json() == {"detail": "reassign_to_department_id is required when mode=reassign"}


def test_delete_department_rejects_missing_reassign_target_department(client: TestClient) -> None:
    department_response = client.post("/departments/", json={"name": "Operations"})
    department_id = department_response.json()["id"]

    response = client.delete(
        f"/departments/{department_id}?mode=reassign&reassign_to_department_id=999"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Reassign department not found"}


def test_create_employee_rejects_short_full_name(client: TestClient) -> None:
    department_response = client.post("/departments/", json={"name": "Operations"})
    department_id = department_response.json()["id"]

    response = client.post(
        f"/departments/{department_id}/employees/",
        json={
            "full_name": "A",
            "position": "Analyst",
            "hired_at": None,
        },
    )

    assert response.status_code == 422


def test_create_employee_rejects_future_hired_at(client: TestClient) -> None:
    department_response = client.post("/departments/", json={"name": "Operations"})
    department_id = department_response.json()["id"]
    future_date = (date.today() + timedelta(days=1)).isoformat()

    response = client.post(
        f"/departments/{department_id}/employees/",
        json={
            "full_name": "Ada Lovelace",
            "position": "Analyst",
            "hired_at": future_date,
        },
    )

    assert response.status_code == 422
