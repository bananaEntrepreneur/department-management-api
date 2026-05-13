from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_department_service
from app.main import app
from app.services.department import DepartmentService


@pytest.fixture
def client(sqlite_session_factory):
    async def override_get_department_service():
        async with sqlite_session_factory() as session:
            yield DepartmentService(session)

    app.dependency_overrides[get_department_service] = override_get_department_service

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
