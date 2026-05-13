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
    root_response = client.post("/departments/", json={"name": "Operations"})

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
