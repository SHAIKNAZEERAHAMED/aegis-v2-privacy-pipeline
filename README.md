# Aegis V2 Privacy Pipeline

Aegis is a research MVP for privacy-preserving video capture. It records a
short video, detects the subject's face, applies classical and adversarial
transformations, calibrates the result against a human recognition limit, and
stores only the protected output.

This project is a proof of concept, not a guarantee of universal anonymity.
The pipeline is resistant only to the configured automated evaluator and the
calibration process used by this application.

## Stack

- Backend: FastAPI, SQLAlchemy, OpenCV, PyTorch, FaceNet
- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Database: SQLite by default
- Storage: local disk by default
- Processing: FastAPI background tasks

## Project structure

```text
backend/    FastAPI API and video-processing pipeline
frontend/   Next.js web application
```

## Requirements

- Windows, macOS, or Linux
- Python 3.10 or newer
- Node.js 18 or newer
- npm
- Internet access on the first backend run for model weights
- Optional: ffmpeg for browser-compatible H.264 output

On Windows, ffmpeg can be installed with:

```powershell
winget install Gyan.FFmpeg.Shared
```

Without ffmpeg, the backend falls back to OpenCV's `mp4v` codec. The pipeline
can still run, but some browsers may not play the resulting video.

## Backend setup on Windows

From the repository root:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` and replace `JWT_SECRET` with a long random value before
using the application outside local development.

Start the API:

```powershell
uvicorn app.main:app --reload --port 8000
```

Open the API documentation at http://localhost:8000/docs.

### Backend setup on macOS or Linux

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Run backend tests

The runtime requirements do not include test tooling. Install it once inside
the active virtual environment:

```powershell
python -m pip install pytest httpx
python -m pytest app/tests -v
```

The test suite covers authentication, session issuance, ownership checks,
capture-duration validation, and the optimization step/backoff schedule.

## Frontend setup

Open a second terminal at the repository root:

```powershell
cd frontend
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

Open http://localhost:3000, create an account, and start a new capture.

For macOS or Linux, use `cp` instead of `Copy-Item` when copying the env file.

## Processing pipeline

1. The browser records a video of up to six seconds.
2. OpenCV extracts frames at approximately 24 FPS.
3. The OpenCV DNN face detector selects the largest detected face.
4. FaceNet creates a baseline embedding for the original face.
5. The optimization engine increases blur, pixelation, noise, compression,
   downsampling, and adversarial perturbation until similarity falls below the
   configured threshold.
6. The user calibrates the result by answering whether the face is still
   recognizable.
7. When the user says it is no longer recognizable, the engine backs off one
   optimization step and locks that profile for the login session.
8. The profile is applied to all detected face-bearing frames.
9. The protected video is reconstructed, validated, stored, and the temporary
   original is removed.

Calibration is reused for later captures in the same login session.

## Configuration

Important backend settings are in `backend/app/core/config.py` and can be
overridden in `.env`:

- `MAX_RECORD_SECONDS`: maximum capture length, default `6`
- `TARGET_FPS`: processing frame rate, default `24`
- `AI_DEFEAT_SIMILARITY_THRESHOLD`: automated recognition threshold, default
  `0.35`
- `MAX_OPTIMIZATION_STEPS`: maximum optimization iterations, default `12`
- `DATABASE_URL`: SQLite by default; can be changed for another SQLAlchemy
  database
- `STORAGE_ROOT`, `TEMP_DIR`, `PROTECTED_DIR`: local storage paths

## Known MVP limitations

- One face is supported per frame; the largest detected face is selected.
- Authentication uses local JWT email/password instead of Firebase.
- Files are stored on local disk instead of object storage.
- Background tasks are in-process and are not a replacement for a queue such
  as Celery or Redis in a multi-instance deployment.
- The production frontend build currently requires a Suspense boundary around
  the calibration page's `useSearchParams()` usage.

## Publish to GitHub

The local folder is not currently a Git repository, and GitHub CLI is not
installed. Use the standard Git commands below.

1. Create a new empty GitHub repository named `aegis-v2-privacy-pipeline`.
   Do not add a README, license, or `.gitignore` during creation because this
   project already contains a README.
2. In PowerShell, from the repository root, run:

```powershell
cd "C:\aegis v2\ai-resistant-video-privacy"
git init
git branch -M main
git add .
git status
git commit -m "Initial Aegis V2 privacy pipeline"
git remote add origin https://github.com/YOUR-USERNAME/aegis-v2-privacy-pipeline.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username. GitHub no longer accepts
account passwords for HTTPS pushes; use a GitHub personal access token when
Git asks for a password, or configure an SSH remote instead.

Before pushing, confirm that local secrets and generated files are ignored.
Never commit `backend/.env`, `backend/venv`, `frontend/.env.local`,
`frontend/node_modules`, model weights, or local storage data.

## License and research note

Add the license and citation information appropriate for your project before
sharing the repository publicly. Review the model and dependency licenses as
well as your obligations for any video data used during testing.
