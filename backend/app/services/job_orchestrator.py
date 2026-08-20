"""
Drives the processing state machine (SRS Section 6) end to end. Runs as a
FastAPI BackgroundTask so the API returns immediately (Performance Req:
no long synchronous HTTP request) while the frontend polls
GET /api/videos/:id/status for progress.

State machine:
CAPTURED -> UPLOADED -> EXTRACTING_FRAMES -> DETECTING_FACES ->
EVALUATING_BASELINE -> OPTIMIZING -> HUMAN_CALIBRATION ->
APPLYING_TRANSFORMATION -> RECONSTRUCTING -> VALIDATING ->
STORING_PROTECTED_VIDEO -> DELETING_ORIGINAL -> COMPLETED
(any stage -> FAILED on error, with temp-data cleanup)
"""
import os
import shutil
import json
from datetime import datetime, timezone

import cv2
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.video import Video
from app.models.processing_job import ProcessingJob
from app.models.face_detection import FaceDetection
from app.models.transformation_profile import TransformationProfile
from app.models.session import Session as LoginSession
from app.services.factory import get_face_detector, get_recognizer, get_transformer, get_optimizer
from app.services.video_processor import extract_frames, reconstruct_video, validate_playable
from app.services.interfaces import TransformParams


def _update(db: DBSession, job: ProcessingJob, video: Video, stage: str, progress: int):
    job.current_stage = stage
    job.progress = progress
    video.status = stage
    db.commit()


def _fail(db: DBSession, job: ProcessingJob, video: Video, message: str, workspace: str = None):
    job.status = "FAILED"
    job.current_stage = "FAILED"
    job.error_message = message
    job.completed_at = datetime.now(timezone.utc)
    video.status = "FAILED"
    db.commit()
    if workspace and os.path.exists(workspace):
        shutil.rmtree(workspace, ignore_errors=True)


def run_processing_job(video_id: str, job_id: str, human_calibration_answer: bool = None):
    """
    Entry point invoked as a background task. `human_calibration_answer` is
    None on the first pass (meaning: this session hasn't calibrated yet, so
    we should stop at HUMAN_CALIBRATION and wait for the frontend to call
    POST /api/calibration, which re-invokes this function with the answer).
    """
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not video or not job:
            return

        workspace = os.path.join(settings.TEMP_DIR, video_id)
        frames_dir = os.path.join(workspace, "frames")
        original_path = os.path.join(workspace, "original.mp4")

        detector = get_face_detector()
        recognizer = get_recognizer()
        transformer = get_transformer()
        optimizer = get_optimizer()

        login_session = db.query(LoginSession).filter(LoginSession.id == video.session_id).first()

        # ---- Resume path: calibration answer just came in ----
        if human_calibration_answer is not None:
            _resume_after_calibration(
                db, video, job, login_session, workspace, frames_dir,
                detector, recognizer, transformer, optimizer, human_calibration_answer,
            )
            return

        # ---- Fresh run ----
        job.status = "RUNNING"
        db.commit()

        _update(db, job, video, "EXTRACTING_FRAMES", 10)
        frame_paths = extract_frames(original_path, frames_dir, int(video.fps or settings.TARGET_FPS))
        if not frame_paths:
            _fail(db, job, video, "No frames could be extracted from capture.", workspace)
            return

        _update(db, job, video, "DETECTING_FACES", 25)
        face_hits = []  # list of (frame_idx, FaceBox)
        for i, fp in enumerate(frame_paths):
            frame = cv2.imread(fp)
            boxes = detector.detect(frame)
            if boxes:
                box = max(boxes, key=lambda b: b.w * b.h)  # largest face, single-face MVP
                face_hits.append((i, box))
                db.add(FaceDetection(
                    video_id=video.id, frame_number=i,
                    bounding_box=json.dumps([box.x, box.y, box.w, box.h]),
                    confidence=box.confidence,
                ))
        db.commit()

        if not face_hits:
            _fail(db, job, video, "No face detected in capture. Please try again.", workspace)
            return

        _update(db, job, video, "EVALUATING_BASELINE", 35)
        rep_idx, rep_box = face_hits[len(face_hits) // 2]  # representative frame = middle detection
        rep_frame = cv2.imread(frame_paths[rep_idx])
        rep_crop = rep_frame[rep_box.y:rep_box.y + rep_box.h, rep_box.x:rep_box.x + rep_box.w]
        original_embedding = recognizer.embed(rep_crop)

        # If this session already has a locked-in profile from an earlier video,
        # skip straight to applying it — FR-013 says calibration happens once per session.
        if login_session.calibration_completed and login_session.calibration_profile_id:
            profile = db.query(TransformationProfile).filter(
                TransformationProfile.id == login_session.calibration_profile_id
            ).first()
            params = TransformParams(
                blur_strength=profile.blur_strength,
                pixelation_strength=profile.pixelation_strength,
                noise_strength=profile.noise_strength,
                compression_quality=profile.compression_quality,
                downsample_factor=profile.downsample_factor,
                adversarial_epsilon=0.5,
            )
            _finish_pipeline(db, job, video, workspace, frames_dir, frame_paths, face_hits,
                              transformer, params)
            return

        # ---- OPTIMIZING: push params up until the recognizer is defeated ----
        _update(db, job, video, "OPTIMIZING", 45)
        params = TransformParams()
        ai_defeated = False
        for _ in range(settings.MAX_OPTIMIZATION_STEPS):
            candidate_frame = transformer.apply(rep_frame, rep_box, params)
            crop = candidate_frame[rep_box.y:rep_box.y + rep_box.h, rep_box.x:rep_box.x + rep_box.w]
            candidate_embedding = recognizer.embed(crop)
            sim = recognizer.similarity(original_embedding, candidate_embedding)
            if sim < settings.AI_DEFEAT_SIMILARITY_THRESHOLD:
                ai_defeated = True
                break
            params = optimizer.next_step(params, ai_defeated=False)

        # Save the shown frame to disk so the calibration endpoint can serve it
        calib_frame = transformer.apply(rep_frame, rep_box, params)
        calib_path = os.path.join(workspace, "calibration_frame.jpg")
        cv2.imwrite(calib_path, calib_frame)

        # persist in-progress params on the job workspace so we can resume later
        with open(os.path.join(workspace, "state.json"), "w") as f:
            json.dump({
                "params": params.__dict__,
                "rep_idx": rep_idx,
                "rep_box": [rep_box.x, rep_box.y, rep_box.w, rep_box.h, rep_box.confidence],
                "original_embedding": original_embedding.tolist(),
                "ai_defeated": ai_defeated,
            }, f)

        _update(db, job, video, "HUMAN_CALIBRATION", 60)
        # Pipeline pauses here. Frontend shows calib_path via GET and the user answers via
        # POST /api/calibration, which calls this module again with human_calibration_answer set.

    except Exception as e:  # noqa: BLE001
        db.rollback()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        video = db.query(Video).filter(Video.id == video_id).first()
        if job and video:
            _fail(db, job, video, f"Processing error: {e}", os.path.join(settings.TEMP_DIR, video_id))
    finally:
        db.close()


def _resume_after_calibration(db, video, job, login_session, workspace, frames_dir,
                               detector, recognizer, transformer, optimizer, human_says_recognizable: bool):
    state_path = os.path.join(workspace, "state.json")
    with open(state_path) as f:
        state = json.load(f)

    params = TransformParams(**state["params"])
    x, y, w, h, conf = state["rep_box"]
    from app.services.interfaces import FaceBox
    rep_box = FaceBox(x=x, y=y, w=w, h=h, confidence=conf)
    frame_paths = sorted(
        os.path.join(frames_dir, f) for f in os.listdir(frames_dir) if f.endswith(".png")
    )
    rep_frame = cv2.imread(frame_paths[state["rep_idx"]])

    if human_says_recognizable:
        # push further — human can still identify them, keep degrading (n -> n+1)
        params = optimizer.next_step(params, ai_defeated=state["ai_defeated"])
        calib_frame = transformer.apply(rep_frame, rep_box, params)
        calib_path = os.path.join(workspace, "calibration_frame.jpg")
        cv2.imwrite(calib_path, calib_frame)
        state["params"] = params.__dict__
        with open(state_path, "w") as f:
            json.dump(state, f)
        _update(db, job, video, "HUMAN_CALIBRATION", 65)
        return  # wait for another calibration round

    # human says NOT recognizable -> back off one step (n-1) and lock it in
    final_params = optimizer.step_back(params)

    profile = TransformationProfile(
        session_id=login_session.id,
        blur_strength=final_params.blur_strength,
        pixelation_strength=final_params.pixelation_strength,
        compression_quality=final_params.compression_quality,
        noise_strength=final_params.noise_strength,
        downsample_factor=final_params.downsample_factor,
        combined_score=None,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    from app.models.calibration_result import CalibrationResult
    db.add(CalibrationResult(
        session_id=login_session.id,
        representative_frame_reference=f"videos/{video.id}/calibration_frame.jpg",
        human_result=False,
        selected_profile_id=profile.id,
    ))
    login_session.calibration_completed = True
    login_session.calibration_profile_id = profile.id
    db.commit()

    face_hits = _reload_all_face_hits(db, video.id, detector, frame_paths)
    _finish_pipeline(db, job, video, workspace, frames_dir, frame_paths, face_hits, transformer, final_params)


def _reload_all_face_hits(db, video_id, detector, frame_paths):
    from app.models.face_detection import FaceDetection
    from app.services.interfaces import FaceBox
    rows = db.query(FaceDetection).filter(FaceDetection.video_id == video_id).all()
    hits = []
    for r in rows:
        x, y, w, h = json.loads(r.bounding_box)
        hits.append((r.frame_number, FaceBox(x=x, y=y, w=w, h=h, confidence=r.confidence)))
    return hits


def _finish_pipeline(db, job, video, workspace, frames_dir, frame_paths, face_hits, transformer, params):
    _update(db, job, video, "APPLYING_TRANSFORMATION", 75)
    face_map = {idx: box for idx, box in face_hits}
    protected_frames_dir = os.path.join(workspace, "protected_frames")
    os.makedirs(protected_frames_dir, exist_ok=True)

    protected_paths = []
    for i, fp in enumerate(frame_paths):
        frame = cv2.imread(fp)
        if i in face_map:
            frame = transformer.apply(frame, face_map[i], params)
        out_path = os.path.join(protected_frames_dir, f"frame_{i:05d}.png")
        cv2.imwrite(out_path, frame)
        protected_paths.append(out_path)

    _update(db, job, video, "RECONSTRUCTING", 85)
    protected_video_path = os.path.join(settings.PROTECTED_DIR, f"{video.id}.mp4")
    reconstruct_video(protected_paths, protected_video_path, int(video.fps or settings.TARGET_FPS))

    _update(db, job, video, "VALIDATING", 92)
    from app.services.video_processor import validate_playable
    if not validate_playable(protected_video_path):
        _fail(db, job, video, "Protected output failed playback validation.", workspace)
        return

    _update(db, job, video, "STORING_PROTECTED_VIDEO", 96)
    video.protected_video_url = f"/api/videos/{video.id}/download"

    _update(db, job, video, "DELETING_ORIGINAL", 98)
    # FR-019: delete the temporary original + all intermediate frames now that
    # the protected output is confirmed persisted.
    shutil.rmtree(workspace, ignore_errors=True)

    job.status = "COMPLETED"
    job.current_stage = "COMPLETED"
    job.progress = 100
    job.completed_at = datetime.now(timezone.utc)
    video.status = "COMPLETED"
    db.commit()
