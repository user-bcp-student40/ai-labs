import base64
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

EXPECTED_MAX_REQUIREMENT_UPLOAD_BYTES = 10_000_000


def token(username: str = "student", role: str = "STUDENT") -> str:
    raw = f"{username}|{role}|{int(time.time()) + 3600}|WORKSHOP_SECRET_2026"
    return base64.b64encode(raw.encode()).decode()


def headers(username: str = "student", role: str = "STUDENT") -> dict[str, str]:
    return {"Authorization": f"Bearer {token(username, role)}"}


def test_lists_seeded_tasks(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers())
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_creates_task_and_summary(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        created = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Add tests", "description": "Improve coverage", "status": "TODO", "priority": "HIGH"},
        )
        summary = client.get("/api/summary", headers=headers())
    assert created.status_code == 201
    assert created.json()["owner"] == "student"
    assert summary.json()["total"] == 3


def test_creates_task_with_apostrophes_in_text_fields(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    payload = {
        "title": "Student's review",
        "description": "Review the owner's requirements",
        "status": "TODO",
        "priority": "HIGH",
    }

    with TestClient(app) as client:
        response = client.post("/api/tasks", headers=headers(), json=payload)

    assert response.status_code == 201
    assert response.json()["title"] == payload["title"]
    assert response.json()["description"] == payload["description"]
    assert response.json()["owner"] == "student"


def test_create_task_preserves_current_defaults_and_string_coercion(
    tmp_path: Path,
) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    payload = {
        "title": None,
        "description": 123,
        "unrecognized": "ignored",
    }

    with TestClient(app) as client:
        response = client.post("/api/tasks", headers=headers(), json=payload)

    assert response.status_code == 201
    assert response.json()["title"] == "None"
    assert response.json()["description"] == "123"
    assert response.json()["status"] == "TODO"
    assert response.json()["priority"] == "MEDIUM"
    assert response.json()["owner"] == "student"
    assert set(response.json()) == {
        "id",
        "title",
        "description",
        "status",
        "owner",
        "priority",
        "createdAt",
    }


def test_summary_preserves_seeded_status_aggregation(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))

    with TestClient(app) as client:
        response = client.get("/api/summary", headers=headers())

    assert response.status_code == 200
    assert response.json() == {
        "owner": "student",
        "total": 2,
        "byStatus": {"TODO": 1, "IN_PROGRESS": 1},
        "highPriorityOpen": 1,
    }


def test_uploads_requirement(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements.txt", b"Login must be accessible", "text/plain")},
        )
    assert response.status_code == 201
    assert (upload_dir / "requirements.txt").exists()


def test_uploads_requirement_at_maximum_size(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    content = b"x" * EXPECTED_MAX_REQUIREMENT_UPLOAD_BYTES

    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements.txt", content, "text/plain")},
        )

    assert response.status_code == 201
    assert response.json() == {
        "owner": "student",
        "fileName": "requirements.txt",
        "storedAt": str(upload_dir / "requirements.txt"),
        "size": EXPECTED_MAX_REQUIREMENT_UPLOAD_BYTES,
    }
    assert (upload_dir / "requirements.txt").stat().st_size == EXPECTED_MAX_REQUIREMENT_UPLOAD_BYTES


def test_rejects_requirement_over_maximum_size(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    content = b"x" * (EXPECTED_MAX_REQUIREMENT_UPLOAD_BYTES + 1)

    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements.txt", content, "text/plain")},
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "File exceeds maximum size"}
    assert not (upload_dir / "requirements.txt").exists()


def test_upload_requires_file(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))

    with TestClient(app) as client:
        response = client.post("/api/requirements", headers=headers())

    assert response.status_code == 422


def test_backend_health_returns_observed_success_fields(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app import main

    class SuccessfulPoolManager:
        def request(self, method: str, url: str, timeout: float):
            assert method == "GET"
            assert timeout == 3.0
            return SimpleNamespace(status=200, data=b"healthy")

    monkeypatch.setattr(main.urllib3, "PoolManager", SuccessfulPoolManager)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))

    with TestClient(app) as client:
        response = client.get("/api/backend-health", headers=headers())

    assert response.status_code == 200
    assert response.json() == {
        "requestedBy": "student",
        "status": 200,
        "body": "healthy",
    }


def test_rejects_invalid_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_invalid_token_response_does_not_expose_exception_details(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))

    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": "Bearer invalid"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_backend_health_response_does_not_expose_exception_details(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app import main

    class FailingPoolManager:
        def request(self, method: str, url: str, timeout: float):
            raise main.urllib3.exceptions.HTTPError("private destination details")

    monkeypatch.setattr(main.urllib3, "PoolManager", FailingPoolManager)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))

    with TestClient(app) as client:
        response = client.get("/api/backend-health", headers=headers())

    assert response.status_code == 200
    assert response.json()["status"] == 0
    assert response.json()["body"] == "Backend health check failed"


def test_concurrent_task_requests_preserve_sqlite_results(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    create_count = 24

    def send_request(index: int, client: TestClient):
        if index % 3 == 0:
            return client.post(
                "/api/tasks",
                headers=headers(),
                json={
                    "title": f"Concurrent task {index}",
                    "description": "Load characterization",
                    "status": "TODO",
                    "priority": "MEDIUM",
                },
            )
        if index % 3 == 1:
            return client.get("/api/tasks", headers=headers())
        return client.get("/api/summary", headers=headers())

    with TestClient(app) as client:
        with ThreadPoolExecutor(max_workers=12) as executor:
            responses = list(
                executor.map(
                    lambda index: send_request(index, client),
                    range(create_count),
                )
            )
        summary = client.get("/api/summary", headers=headers())

    assert all(response.status_code in {200, 201} for response in responses)
    assert summary.json()["total"] == 2 + create_count // 3


def test_closes_database_connection_on_shutdown(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))

    with TestClient(app):
        pass

    with pytest.raises(sqlite3.ProgrammingError):
        app.state.connection.execute("SELECT 1")
