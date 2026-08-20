from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    session_id: str


class VideoOut(BaseModel):
    id: str
    status: str
    duration: Optional[float]
    fps: Optional[float]
    protected_video_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class StatusResponse(BaseModel):
    status: str
    progress: int
    stage: str
    error_message: Optional[str] = None
    calibration_pending: bool = False


class CalibrationPrompt(BaseModel):
    video_id: str
    frame_url: str


class CalibrationAnswer(BaseModel):
    video_id: str
    recognizable: bool
