"""
Replaceable interfaces for the ML pipeline (SRS Section 13: Modularity Requirements).

Swap any implementation without touching API routes, DB access, or the frontend —
that's the whole point of these ABCs. Want to plug in a different face detector,
a different embedding model, or a real trained RL policy instead of the
PGD/classical optimizer? Implement the relevant interface and change one line
in app/services/factory.py.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import numpy as np


@dataclass
class FaceBox:
    x: int
    y: int
    w: int
    h: int
    confidence: float


@dataclass
class TransformParams:
    blur_strength: float = 0.0          # 0 - 1
    pixelation_strength: float = 0.0    # 0 - 1
    noise_strength: float = 0.0         # 0 - 1
    compression_quality: float = 100.0  # 100 (none) -> 1 (max)
    downsample_factor: float = 1.0      # 1.0 (none) -> 0.1 (heavy)
    adversarial_epsilon: float = 0.0    # PGD step budget, 0 - 1 (scaled internally)

    def strength_scalar(self) -> float:
        """Single number representing overall degradation, used to order/step iterations."""
        return (
            self.blur_strength
            + self.pixelation_strength
            + self.noise_strength
            + (1 - self.downsample_factor)
            + (100 - self.compression_quality) / 100
            + self.adversarial_epsilon
        )


class FaceDetector(ABC):
    @abstractmethod
    def detect(self, frame_bgr: np.ndarray) -> List[FaceBox]:
        """Return detected face boxes with confidence for a single BGR frame."""
        raise NotImplementedError


class FaceRecognizer(ABC):
    @abstractmethod
    def embed(self, face_crop_bgr: np.ndarray) -> np.ndarray:
        """Return a fixed-length embedding vector for a cropped face."""
        raise NotImplementedError

    @abstractmethod
    def similarity(self, embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
        """Return similarity in [-1, 1] (cosine). Higher = more recognizable as same identity."""
        raise NotImplementedError


class PrivacyTransformer(ABC):
    @abstractmethod
    def apply(self, frame_bgr: np.ndarray, box: FaceBox, params: TransformParams) -> np.ndarray:
        """Return a copy of frame_bgr with the face region (only) transformed per params."""
        raise NotImplementedError


class OptimizationEngine(ABC):
    @abstractmethod
    def next_step(self, current: TransformParams, ai_defeated: bool) -> TransformParams:
        """Given current params and whether the recognizer was defeated, return the next
        (typically stronger) set of params to try."""
        raise NotImplementedError

    @abstractmethod
    def step_back(self, current: TransformParams) -> TransformParams:
        """Return the previous, slightly weaker params (used for the human-limit n-1 backoff)."""
        raise NotImplementedError
