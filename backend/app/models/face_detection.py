from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import gen_uuid


class FaceDetection(Base):
    __tablename__ = "face_detections"

    id = Column(String, primary_key=True, default=gen_uuid)
    video_id = Column(String, ForeignKey("videos.id"), nullable=False)
    frame_number = Column(Integer, nullable=False)
    bounding_box = Column(String, nullable=False)  # JSON string: [x, y, w, h]
    confidence = Column(Float, nullable=False)

    video = relationship("Video", back_populates="face_detections")
