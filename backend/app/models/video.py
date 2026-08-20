from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import gen_uuid


class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)

    # CAPTURED, UPLOADED, EXTRACTING_FRAMES, DETECTING_FACES, EVALUATING_BASELINE,
    # OPTIMIZING, HUMAN_CALIBRATION, APPLYING_TRANSFORMATION, RECONSTRUCTING,
    # VALIDATING, STORING_PROTECTED_VIDEO, DELETING_ORIGINAL, COMPLETED, FAILED
    status = Column(String, default="CAPTURED", index=True)

    duration = Column(Float, nullable=True)
    fps = Column(Float, nullable=True)
    protected_video_url = Column(String, nullable=True)  # only set once protected output exists
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="videos")
    session = relationship("Session", back_populates="videos")
    processing_jobs = relationship("ProcessingJob", back_populates="video", cascade="all, delete-orphan")
    face_detections = relationship("FaceDetection", back_populates="video", cascade="all, delete-orphan")
