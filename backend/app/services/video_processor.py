"""
FR-008 Frame Extraction, FR-016 Reconstruction, FR-017 Validation.
"""
import os
import cv2
import subprocess


def extract_frames(video_path: str, out_dir: str, target_fps: int) -> list:
    """Extract ordered frames from video_path into out_dir. Returns sorted frame paths."""
    os.makedirs(out_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    src_fps = cap.get(cv2.CAP_PROP_FPS) or target_fps
    frame_interval = max(1, round(src_fps / target_fps))

    frame_paths = []
    idx = 0
    saved = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % frame_interval == 0:
            path = os.path.join(out_dir, f"frame_{saved:05d}.png")
            cv2.imwrite(path, frame)
            frame_paths.append(path)
            saved += 1
        idx += 1
    cap.release()
    return frame_paths


def reconstruct_video(frame_paths: list, out_path: str, fps: int) -> str:
    """Reconstruct an ordered list of frame image paths into a playable mp4."""
    if not frame_paths:
        raise ValueError("No frames to reconstruct")

    first = cv2.imread(frame_paths[0])
    h, w = first.shape[:2]

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
    for p in frame_paths:
        frame = cv2.imread(p)
        writer.write(frame)
    writer.release()

    # Re-mux via ffmpeg for broad browser compatibility (H.264) if ffmpeg is available
    h264_path = out_path.replace(".mp4", "_h264.mp4")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", out_path,
                "-vcodec", "libx264", "-pix_fmt", "yuv420p",
                "-loglevel", "error", h264_path,
            ],
            check=True,
        )
        os.replace(h264_path, out_path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # ffmpeg not available / failed — fall back to the mp4v-encoded file as-is
        pass

    return out_path


def validate_playable(video_path: str) -> bool:
    """FR-017: confirm the protected output can actually be opened/read before persistence."""
    cap = cv2.VideoCapture(video_path)
    ok = cap.isOpened()
    if ok:
        ok, _ = cap.read()
    cap.release()
    return ok
