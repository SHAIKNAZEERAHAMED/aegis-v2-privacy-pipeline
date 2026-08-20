from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import gen_uuid


class CalibrationResult(Base):
    __tablename__ = "calibration_results"

    id = Column(String, primary_key=True, default=gen_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    representative_frame_reference = Column(String, nullable=False)  # path/key to the shown frame
    human_result = Column(Boolean, nullable=False)  # True = still recognizable to human
    selected_profile_id = Column(String, ForeignKey("transformation_profiles.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
