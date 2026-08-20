from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import gen_uuid


class TransformationProfile(Base):
    __tablename__ = "transformation_profiles"

    id = Column(String, primary_key=True, default=gen_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    blur_strength = Column(Float, default=0.0)
    pixelation_strength = Column(Float, default=0.0)
    compression_quality = Column(Float, default=100.0)  # lower = more compressed
    noise_strength = Column(Float, default=0.0)
    downsample_factor = Column(Float, default=1.0)
    combined_score = Column(Float, nullable=True)  # cosine similarity to original embedding
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
