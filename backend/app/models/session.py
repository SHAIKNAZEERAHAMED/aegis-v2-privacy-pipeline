from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import gen_uuid


class Session(Base):
    """
    Represents a single login session. Human calibration (FR-013) happens
    at most once per session, and its resulting profile is reused for every
    subsequent video captured within that same session.
    """
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    login_started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    calibration_completed = Column(Boolean, default=False)
    calibration_profile_id = Column(String, ForeignKey("transformation_profiles.id"), nullable=True)

    user = relationship("User", back_populates="sessions")
    videos = relationship("Video", back_populates="session")
