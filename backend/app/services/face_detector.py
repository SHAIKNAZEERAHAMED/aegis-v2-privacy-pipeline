"""
FaceDetector implementation.

Uses OpenCV's res10 SSD DNN face detector — lightweight, no GPU needed, ships
with opencv-python via a small prototxt + caffemodel pair. Swap this for
mediapipe / RetinaFace / YOLO-face later by implementing the same interface.
"""
import os
import urllib.request
import numpy as np
import cv2

from app.services.interfaces import FaceDetector, FaceBox

_MODEL_DIR = os.path.join(os.path.dirname(__file__), "_weights")
_PROTOTXT = os.path.join(_MODEL_DIR, "deploy.prototxt")
_MODEL = os.path.join(_MODEL_DIR, "res10_300x300_ssd_iter_140000.caffemodel")

_PROTOTXT_URL = (
    "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
)
_MODEL_URL = (
    "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/"
    "res10_300x300_ssd_iter_140000.caffemodel"
)


def _ensure_weights():
    os.makedirs(_MODEL_DIR, exist_ok=True)
    if not os.path.exists(_PROTOTXT):
        urllib.request.urlretrieve(_PROTOTXT_URL, _PROTOTXT)
    if not os.path.exists(_MODEL):
        urllib.request.urlretrieve(_MODEL_URL, _MODEL)


class OpenCVDnnFaceDetector(FaceDetector):
    def __init__(self, confidence_threshold: float = 0.6):
        _ensure_weights()
        self.net = cv2.dnn.readNetFromCaffe(_PROTOTXT, _MODEL)
        self.confidence_threshold = confidence_threshold

    def detect(self, frame_bgr: np.ndarray):
        h, w = frame_bgr.shape[:2]
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame_bgr, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0)
        )
        self.net.setInput(blob)
        detections = self.net.forward()

        boxes = []
        for i in range(detections.shape[2]):
            confidence = float(detections[0, 0, i, 2])
            if confidence < self.confidence_threshold:
                continue
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            x1, y1, x2, y2 = box.astype(int)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            if x2 <= x1 or y2 <= y1:
                continue
            boxes.append(FaceBox(
                x=int(x1),
                y=int(y1),
                w=int(x2 - x1),
                h=int(y2 - y1),
                confidence=confidence,
            ))
        return boxes
