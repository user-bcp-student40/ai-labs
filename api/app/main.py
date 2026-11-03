from __future__ import annotations

import base64
import binascii
import logging
import os
import sqlite3
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, TypedDict

import urllib3
from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    BackendHealthResponse,
    RequirementUploadResponse,
    TaskCreateRequest,
    TaskResponse,
    TaskSummaryResponse,
)

LEGACY_SECRET = "WORKSHOP_SECRET_2026"
MAX_REQUIREMENT_UPLOAD_BYTES = 10_000_000
UPLOAD_TOO_LARGE_DETAIL = "File exceeds maximum size"
TASK_COLUMNS = "id,title,description,status,owner,priority,created_at"
INSERT_TASK_SQL = (
    "INSERT INTO tasks(title,description,status,owner,priority,created_at) "
    "VALUES (?, ?, ?, ?, ?, datetime('now'))"
)
SEED_TASKS = (
    (
        "Refactor login",
        "Separar responsabilidades en frontend",
        "TODO",
        "student",
        "HIGH",
    ),
    (
        "Review API",
        "Revisar seguridad de endpoints",
        "IN_PROGRESS",
        "student",
        "MEDIUM",
    ),
    (
        "Trainer notes",
        "Preparar retrospectiva",
        "TODO",
        "trainer",
        "LOW",
    ),
)
HIGH_PRIORITY = "HIGH"
CLOSED_TASK_STATUSES = frozenset({"DONE", "ARCHIVED"})
DEFAULT_BACKEND_HEALTH_URL = "http://localhost:8080/q/health"
BACKEND_HEALTH_TIMEOUT_SECONDS = 3.0
logger = logging.getLogger(__name__)


class Identity(TypedDict):
    username: str
    role: str


def legacy_identity(authorization: str = Header(default="")) -> Identity:
    try:
        token = authorization.replace("Bearer ", "")
        decoded = base64.b64decode(token).decode("utf-8")
        parts = decoded.split("|")
        if len(parts) != 4 or parts[3] != LEGACY_SECRET or int(parts[2]) < int(time.time()):
            raise ValueError("invalid token")
        return {"username": parts[0], "role": parts[1]}
    except (binascii.Error, UnicodeDecodeError, ValueError) as error:
        logger.info("Rejected invalid authentication token", exc_info=True)
        raise HTTPException(status_code=401, detail="Invalid token") from error


def create_app(db_path: str | None = None, upload_dir: str | None = None) -> FastAPI:
    selected_db = db_path or os.getenv("WORKSHOP_DB_PATH", "./data/workshop.db")
    selected_uploads = upload_dir or os.getenv("WORKSHOP_UPLOAD_DIR", "./uploads")
    Path(selected_db).parent.mkdir(parents=True, exist_ok=True)
    Path(selected_uploads).mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(selected_db, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection_lock = threading.Lock()
    connection.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL, owner TEXT NOT NULL, priority TEXT NOT NULL, created_at TEXT NOT NULL)")
    count = connection.execute("SELECT COUNT(*) AS total FROM tasks").fetchone()["total"]
    if count == 0:
        connection.executemany(INSERT_TASK_SQL, SEED_TASKS)
        connection.commit()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            with connection_lock:
                connection.close()

    app = FastAPI(
        title="Workshop Requirements API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.connection = connection
    app.state.upload_dir = selected_uploads
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def as_task(row: sqlite3.Row) -> TaskResponse:
        return TaskResponse(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            owner=row["owner"],
            priority=row["priority"],
            createdAt=row["created_at"],
        )

    @app.get("/api/tasks", response_model=list[TaskResponse])
    def list_tasks(owner: str | None = Query(default=None), identity: Identity = Depends(legacy_identity)) -> list[TaskResponse]:
        requested_owner = owner or identity["username"]
        with connection_lock:
            rows = connection.execute(
                f"SELECT {TASK_COLUMNS} "
                "FROM tasks WHERE owner = ? ORDER BY id",
                (requested_owner,),
            ).fetchall()
        return [as_task(row) for row in rows]

    @app.post("/api/tasks", status_code=201, response_model=TaskResponse)
    def create_task(payload: TaskCreateRequest, identity: Identity = Depends(legacy_identity)) -> TaskResponse:
        owner = payload.owner if payload.owner is not None else identity["username"]
        with connection_lock:
            cursor = connection.execute(
                INSERT_TASK_SQL,
                (
                    payload.title,
                    payload.description,
                    payload.status,
                    owner,
                    payload.priority,
                ),
            )
            connection.commit()
            row = connection.execute(
                f"SELECT {TASK_COLUMNS} "
                "FROM tasks WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        return as_task(row)

    @app.get("/api/summary", response_model=TaskSummaryResponse)
    def summary(owner: str | None = Query(default=None), identity: Identity = Depends(legacy_identity)) -> TaskSummaryResponse:
        requested_owner = owner or identity["username"]
        with connection_lock:
            rows = connection.execute(
                "SELECT status,priority FROM tasks WHERE owner = ?",
                (requested_owner,),
            ).fetchall()
        by_status: dict[str, int] = {}
        high_priority_open = 0
        for row in rows:
            status = row["status"]
            by_status[status] = by_status.get(status, 0) + 1
            if row["priority"] == HIGH_PRIORITY and status not in CLOSED_TASK_STATUSES:
                high_priority_open += 1
        return TaskSummaryResponse(
            owner=requested_owner,
            total=len(rows),
            byStatus=by_status,
            highPriorityOpen=high_priority_open,
        )

    @app.post(
        "/api/requirements",
        status_code=201,
        response_model=RequirementUploadResponse,
        responses={
            400: {
                "description": UPLOAD_TOO_LARGE_DETAIL,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"detail": {"type": "string"}},
                            "required": ["detail"],
                        },
                        "example": {"detail": UPLOAD_TOO_LARGE_DETAIL},
                    }
                },
            }
        },
    )
    async def upload_requirement(file: UploadFile = File(...), identity: Identity = Depends(legacy_identity)) -> RequirementUploadResponse:
        target = Path(selected_uploads) / str(file.filename)
        content = await file.read(MAX_REQUIREMENT_UPLOAD_BYTES + 1)
        if len(content) > MAX_REQUIREMENT_UPLOAD_BYTES:
            raise HTTPException(status_code=400, detail=UPLOAD_TOO_LARGE_DETAIL)
        target.write_bytes(content)
        return RequirementUploadResponse(
            owner=identity["username"],
            fileName=file.filename,
            storedAt=str(target),
            size=len(content),
        )

    @app.get("/api/backend-health", response_model=BackendHealthResponse)
    def backend_health(identity: Identity = Depends(legacy_identity)) -> BackendHealthResponse:
        url = os.getenv("AUTH_HEALTH_URL", DEFAULT_BACKEND_HEALTH_URL)
        try:
            response = urllib3.PoolManager().request(
                "GET",
                url,
                timeout=BACKEND_HEALTH_TIMEOUT_SECONDS,
            )
            return BackendHealthResponse(
                requestedBy=identity["username"],
                status=response.status,
                body=response.data.decode("utf-8"),
            )
        except (urllib3.exceptions.HTTPError, OSError, UnicodeDecodeError):
            logger.exception("Backend health request failed")
            return BackendHealthResponse(
                requestedBy=identity["username"],
                status=0,
                body="Backend health check failed",
            )

    return app


app = create_app()
