import os
import shutil

import cv2
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user, get_current_user_flexible
from app.models.user import User
from app.models.video import Video
from app.models.processing_job import ProcessingJob
from app.models.session import Session as LoginSession
from app.schemas.schemas import VideoOut, StatusResponse
from app.services.job_orchestrator import run_processing_job

router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.post("", response_model=VideoOut)
def create_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: DBSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    FR-005/FR-006: accepts a <=6s browser capture. The raw file is written
    ONLY to the temporary per-video workspace (never to protected storage).
    """
    session_id = user.current_session_id

    video = Video(user_id=user.id, session_id=session_id, status="CAPTURED")
    db.add(video)
    db.commit()
    db.refresh(video)

    workspace = os.path.join(settings.TEMP_DIR, video.id)
    os.makedirs(workspace, exist_ok=True)
    original_path = os.path.join(workspace, "original.mp4")

    with open(original_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    cap = cv2.VideoCapture(original_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or settings.TARGET_FPS
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    duration = frame_count / fps if fps else None
    cap.release()

    if duration and duration > settings.MAX_RECORD_SECONDS + 1:  # +1s tolerance for encoder overhead
        shutil.rmtree(workspace, ignore_errors=True)
        db.delete(video)
        db.commit()
        raise HTTPException(status_code=400, detail=f"Capture exceeds {settings.MAX_RECORD_SECONDS}s limit")

    video.fps = fps
    video.duration = duration
    video.status = "UPLOADED"
    db.commit()
    db.refresh(video)

    return video


@router.post("/{video_id}/process", response_model=StatusResponse)
def start_processing(
    video_id: str,
    background_tasks: BackgroundTasks,
    db: DBSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    video = _get_owned_video(db, video_id, user)
    if video.status not in ("UPLOADED", "FAILED"):
        raise HTTPException(status_code=400, detail=f"Video is not in a processable state ({video.status})")

    job = ProcessingJob(video_id=video.id, status="PENDING", current_stage="UPLOADED", progress=0)
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(run_processing_job, video.id, job.id, None)

    return StatusResponse(status="RUNNING", progress=0, stage="UPLOADED")


@router.get("/{video_id}/status", response_model=StatusResponse)
def get_status(video_id: str, db: DBSession = Depends(get_db), user: User = Depends(get_current_user)):
    video = _get_owned_video(db, video_id, user)
    job = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.video_id == video.id)
        .order_by(ProcessingJob.started_at.desc())
        .first()
    )
    if not job:
        return StatusResponse(status=video.status, progress=0, stage=video.status)

    return StatusResponse(
        status=job.status,
        progress=job.progress,
        stage=job.current_stage,
        error_message=job.error_message,
        calibration_pending=(job.current_stage == "HUMAN_CALIBRATION"),
    )


@router.get("", response_model=list[VideoOut])
def list_videos(db: DBSession = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Video).filter(Video.user_id == user.id).order_by(Video.created_at.desc()).all()


@router.get("/{video_id}", response_model=VideoOut)
def get_video(video_id: str, db: DBSession = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_owned_video(db, video_id, user)


@router.get("/{video_id}/download")
def download_video(
    video_id: str, db: DBSession = Depends(get_db), user: User = Depends(get_current_user_flexible)
):
    video = _get_owned_video(db, video_id, user)
    if video.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Protected video not ready yet")

    path = os.path.join(settings.PROTECTED_DIR, f"{video.id}.mp4")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Protected file missing")

    return FileResponse(path, media_type="video/mp4", filename=f"protected_{video.id}.mp4")


@router.delete("/{video_id}")
def delete_video(video_id: str, db: DBSession = Depends(get_db), user: User = Depends(get_current_user)):
    video = _get_owned_video(db, video_id, user)
    path = os.path.join(settings.PROTECTED_DIR, f"{video.id}.mp4")
    if os.path.exists(path):
        os.remove(path)
    db.delete(video)
    db.commit()
    return {"deleted": True}


def _get_owned_video(db: DBSession, video_id: str, user: User) -> Video:
    """FR-023/Security Req: ownership check, not a trusted client-supplied ID."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this video")
    return video
