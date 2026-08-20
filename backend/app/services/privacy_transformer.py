"""
PrivacyTransformer implementation.

Applies transformations ONLY inside the detected face bounding box (padded
slightly) so the rest of the frame — background, body, context an investigator
or family member needs — stays untouched. Two layers, applied together:

  1. Classical degradation: gaussian blur, pixelation, additive noise, JPEG
     recompression, downsample/upsample. These are what keep the frame human-
     interpretable-but-softened, and they're what FR-011/FR-012 primarily
     describe.

  2. Adversarial perturbation (PGD): small, targeted pixel-level noise computed
     via gradient ascent on the embedding distance from the original, using the
     FaceRecognizer's differentiable embed_tensor_grad(). This is the piece
     that specifically confuses the *embedding model* even when the frame still
     looks reasonably clear to a human — the classical transforms alone won't
     reliably do that against a strong recognizer.
"""
import numpy as np
import cv2
import torch

from app.services.interfaces import PrivacyTransformer, FaceBox, TransformParams
from app.services.face_recognizer import FacenetRecognizer, _device


class CombinedPrivacyTransformer(PrivacyTransformer):
    def __init__(self, recognizer: FacenetRecognizer):
        self.recognizer = recognizer

    def _pad_box(self, box: FaceBox, frame_shape, pad_ratio=0.15):
        h, w = frame_shape[:2]
        pad_x = int(box.w * pad_ratio)
        pad_y = int(box.h * pad_ratio)
        x1 = max(0, box.x - pad_x)
        y1 = max(0, box.y - pad_y)
        x2 = min(w, box.x + box.w + pad_x)
        y2 = min(h, box.y + box.h + pad_y)
        return x1, y1, x2, y2

    def _classical(self, crop: np.ndarray, params: TransformParams) -> np.ndarray:
        out = crop.copy()
        h, w = out.shape[:2]

        # Downsample/upsample (loses fine detail)
        if params.downsample_factor < 1.0:
            small_w = max(1, int(w * params.downsample_factor))
            small_h = max(1, int(h * params.downsample_factor))
            out = cv2.resize(out, (small_w, small_h), interpolation=cv2.INTER_LINEAR)
            out = cv2.resize(out, (w, h), interpolation=cv2.INTER_LINEAR)

        # Pixelation
        if params.pixelation_strength > 0:
            factor = max(0.02, 1.0 - params.pixelation_strength)
            px_w = max(1, int(w * factor))
            px_h = max(1, int(h * factor))
            out = cv2.resize(out, (px_w, px_h), interpolation=cv2.INTER_LINEAR)
            out = cv2.resize(out, (w, h), interpolation=cv2.INTER_NEAREST)

        # Gaussian blur
        if params.blur_strength > 0:
            k = max(1, int(params.blur_strength * 25))
            k = k if k % 2 == 1 else k + 1
            out = cv2.GaussianBlur(out, (k, k), 0)

        # Additive noise
        if params.noise_strength > 0:
            noise = np.random.normal(0, params.noise_strength * 40, out.shape).astype(np.float32)
            out = np.clip(out.astype(np.float32) + noise, 0, 255).astype(np.uint8)

        # JPEG recompression artifact
        if params.compression_quality < 100:
            q = max(1, int(params.compression_quality))
            ok, enc = cv2.imencode(".jpg", out, [int(cv2.IMWRITE_JPEG_QUALITY), q])
            if ok:
                out = cv2.imdecode(enc, cv2.IMREAD_COLOR)

        return out

    def _adversarial(self, crop: np.ndarray, params: TransformParams, steps: int = 5) -> np.ndarray:
        if params.adversarial_epsilon <= 0:
            return crop

        orig_tensor = self.recognizer._preprocess(crop).detach()
        with torch.no_grad():
            orig_emb = self.recognizer.model(orig_tensor)

        adv = orig_tensor.clone().detach().requires_grad_(True)
        eps = params.adversarial_epsilon * 0.3  # scale into a sane pixel-space budget
        step_size = eps / steps

        for _ in range(steps):
            emb = self.recognizer.model(adv)
            # maximize distance from original embedding (i.e. minimize cosine sim)
            loss = torch.nn.functional.cosine_similarity(emb, orig_emb).mean()
            self.recognizer.model.zero_grad(set_to_none=True)
            loss.backward()
            with torch.no_grad():
                adv = adv - step_size * adv.grad.sign()
                delta = torch.clamp(adv - orig_tensor, -eps, eps)
                adv = torch.clamp(orig_tensor + delta, -1, 1)
            adv.requires_grad_(True)

        adv_np = adv.detach().squeeze(0).cpu().permute(1, 2, 0).numpy()
        adv_np = np.clip((adv_np * 128.0) + 127.5, 0, 255).astype(np.uint8)
        adv_np = cv2.cvtColor(adv_np, cv2.COLOR_RGB2BGR)
        adv_np = cv2.resize(adv_np, (crop.shape[1], crop.shape[0]))
        return adv_np

    def apply(self, frame_bgr: np.ndarray, box: FaceBox, params: TransformParams) -> np.ndarray:
        out_frame = frame_bgr.copy()
        x1, y1, x2, y2 = self._pad_box(box, frame_bgr.shape)
        crop = out_frame[y1:y2, x1:x2]
        if crop.size == 0:
            return out_frame

        crop = self._classical(crop, params)
        crop = self._adversarial(crop, params)

        out_frame[y1:y2, x1:x2] = crop
        return out_frame
