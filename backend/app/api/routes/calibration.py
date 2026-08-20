import os

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user, get_current_user_flexible
from app.models.user import User
from app.models.video import Video
from app.models.session import Session as LoginSession
from app.schemas.schemas import CalibrationAnswer
from app.services.job_orchestrator import run_processing_job

router = APIRouter(prefix="/api/calibration", tags=["calibration"])


@router.get("/{video_id}/frame")
def get_calibration_frame(
    video_id: str, db: DBSession = Depends(get_db), user: User = Depends(get_current_user_flexible)
):
    video = db.query(Video).filter(Video.id == video_id, Video.user_id == user.id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    path = os.path.join(settings.TEMP_DIR, video_id, "calibration_frame.jpg")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No calibration frame available for this video")

    return FileResponse(path, media_type="image/jpeg")


@router.post("")
def submit_calibration(
    payload: CalibrationAnswer,
    background_tasks: BackgroundTasks,
    db: DBSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    FR-013/FR-014: human recognizability feedback, once per login session.
    `recognizable=True` -> keep degrading further; `recognizable=False` ->
    lock the profile one step back (n-1) and finish the pipeline.
    """
    video = db.query(Video).filter(Video.id == payload.video_id, Video.user_id == user.id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    from app.models.processing_job import ProcessingJob
    job = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.video_id == video.id)
        .order_by(ProcessingJob.started_at.desc())
        .first()
    )
    if not job or job.current_stage != "HUMAN_CALIBRATION":
        raise HTTPException(status_code=400, detail="Video is not awaiting calibration")

    background_tasks.add_task(run_processing_job, video.id, job.id, payload.recognizable)
    return {"accepted": True}


@router.get("")
def get_session_calibration(db: DBSession = Depends(get_db), user: User = Depends(get_current_user)):
    session = db.query(LoginSession).filter(LoginSession.id == user.current_session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "calibration_completed": session.calibration_completed,
        "calibration_profile_id": session.calibration_profile_id,
    }
