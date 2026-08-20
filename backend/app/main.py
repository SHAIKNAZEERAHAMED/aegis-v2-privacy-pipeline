from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.core.config import settings
from app.api.routes import auth, videos, calibration
from app.services.retention import start_retention_sweeper, stop_retention_sweeper
import app.models  # noqa: F401 ensures all models are registered before create_all

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)


@app.on_event("startup")
def _on_startup():
    # Backstop cleanup: purge any temp workspace older than
    # TEMP_RETENTION_MINUTES in case a job's normal cleanup never ran.
    start_retention_sweeper()


@app.on_event("shutdown")
def _on_shutdown():
    stop_retention_sweeper()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend dev origin; tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(videos.router)
app.include_router(calibration.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}
