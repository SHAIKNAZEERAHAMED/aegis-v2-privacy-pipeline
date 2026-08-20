"""
FaceRecognizer implementation.

Uses facenet-pytorch's InceptionResnetV1 pretrained on VGGFace2 to produce
512-d face embeddings. This IS the "automated recognition evaluator" your
transformations are optimizing against (SRS Section 18: results are reported
as resistance against this configured evaluator, not as universal immunity).
"""
import numpy as np
import torch
import cv2
from facenet_pytorch import InceptionResnetV1

from app.services.interfaces import FaceRecognizer

_device = "cuda" if torch.cuda.is_available() else "cpu"


class FacenetRecognizer(FaceRecognizer):
    def __init__(self):
        self.model = InceptionResnetV1(pretrained="vggface2").eval().to(_device)

    def _preprocess(self, face_crop_bgr: np.ndarray) -> torch.Tensor:
        face = cv2.resize(face_crop_bgr, (160, 160))
        face_rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
        tensor = torch.from_numpy(face_rgb).permute(2, 0, 1).float()
        tensor = (tensor - 127.5) / 128.0
        return tensor.unsqueeze(0).to(_device)

    def embed(self, face_crop_bgr: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            tensor = self._preprocess(face_crop_bgr)
            emb = self.model(tensor)
        return emb.squeeze(0).cpu().numpy()

    def embed_tensor_grad(self, face_crop_bgr: np.ndarray) -> torch.Tensor:
        """Same as embed() but keeps the input tensor differentiable, for PGD attacks."""
        tensor = self._preprocess(face_crop_bgr)
        tensor.requires_grad_(True)
        return tensor

    def similarity(self, embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
        a = embedding_a / (np.linalg.norm(embedding_a) + 1e-8)
        b = embedding_b / (np.linalg.norm(embedding_b) + 1e-8)
        return float(np.dot(a, b))
