"""
Single place that decides which concrete implementation backs each interface.
Change an implementation here and nowhere else needs to change (SRS Section 13).
"""
from functools import lru_cache

from app.services.face_detector import OpenCVDnnFaceDetector
from app.services.face_recognizer import FacenetRecognizer
from app.services.privacy_transformer import CombinedPrivacyTransformer
from app.services.optimization_engine import ScheduledOptimizationEngine
from app.core.config import settings


@lru_cache()
def get_face_detector() -> OpenCVDnnFaceDetector:
    return OpenCVDnnFaceDetector()


@lru_cache()
def get_recognizer() -> FacenetRecognizer:
    return FacenetRecognizer()


@lru_cache()
def get_transformer() -> CombinedPrivacyTransformer:
    return CombinedPrivacyTransformer(get_recognizer())


@lru_cache()
def get_optimizer() -> ScheduledOptimizationEngine:
    return ScheduledOptimizationEngine(max_steps=settings.MAX_OPTIMIZATION_STEPS)
