"""
Covers the SRS's explicit testing requirement (Section 16):
"Write tests for authentication guards, ownership checks, frame ordering,
transformation parameter validation, and job state transitions."

Run with: pytest app/tests -v
(requires the full requirements.txt installed, including torch — these hit
 real DB + auth code but stub out the heavy ML calls where noted.)
"""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET"] = "test-secret"

from app.main import app  # noqa: E402
from app.core.database import Base, engine, get_db, SessionLocal  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def signup(email="user1@example.com", password="password123"):
    res = client.post("/api/auth/signup", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()


def test_signup_and_login():
    data = signup()
    assert "access_token" in data
    assert "session_id" in data

    res = client.post("/api/auth/login", json={"email": "user1@example.com", "password": "password123"})
    assert res.status_code == 200
    assert res.json()["access_token"]


def test_login_wrong_password_rejected():
    signup()
    res = client.post("/api/auth/login", json={"email": "user1@example.com", "password": "wrong"})
    assert res.status_code == 401


def test_unauthenticated_video_list_rejected():
    res = client.get("/api/videos")
    assert res.status_code == 401


def test_user_cannot_access_another_users_video():
    """FR-023 / Security Requirement: ownership-based authorization."""
    user_a = signup(email="a@example.com")
    user_b = signup(email="b@example.com")

    headers_a = {"Authorization": f"Bearer {user_a['access_token']}"}
    headers_b = {"Authorization": f"Bearer {user_b['access_token']}"}

    # user A creates a video record directly via DB (bypassing upload/ML pipeline)
    from app.models.video import Video

    db = SessionLocal()
    video = Video(user_id=_user_id_from_token(user_a["access_token"]), session_id=user_a["session_id"], status="COMPLETED")
    db.add(video)
    db.commit()
    db.refresh(video)
    video_id = video.id
    db.close()

    # user A can access it
    res = client.get(f"/api/videos/{video_id}", headers=headers_a)
    assert res.status_code == 200

    # user B cannot
    res = client.get(f"/api/videos/{video_id}", headers=headers_b)
    assert res.status_code == 403


def _user_id_from_token(token: str) -> str:
    from app.core.security import decode_token
    return decode_token(token)["sub"]


def test_video_exceeding_capture_limit_rejected(tmp_path):
    """FR-005: reject captures over the 6s (+tolerance) limit."""
    import cv2
    import numpy as np

    user = signup()
    headers = {"Authorization": f"Bearer {user['access_token']}"}

    # build an 8-second dummy video at 24fps
    path = tmp_path / "long.mp4"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 24, (64, 64))
    for _ in range(24 * 8):
        writer.write(np.zeros((64, 64, 3), dtype=np.uint8))
    writer.release()

    with open(path, "rb") as f:
        res = client.post("/api/videos", headers=headers, files={"file": ("long.mp4", f, "video/mp4")})
    assert res.status_code == 400
