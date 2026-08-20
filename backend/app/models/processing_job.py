from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import gen_uuid


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String, primary_key=True, default=gen_uuid)
    video_id = Column(String, ForeignKey("videos.id"), nullable=False)
    status = Column(String, default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    current_stage = Column(String, default="CAPTURED")
    progress = Column(Integer, default=0)  # 0-100
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)

    video = relationship("Video", back_populates="processing_jobs")
