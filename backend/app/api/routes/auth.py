from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.models.session import Session as LoginSession
from app.schemas.schemas import SignupRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: DBSession = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    return _issue_session(db, user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return _issue_session(db, user)


def _issue_session(db: DBSession, user: User) -> TokenResponse:
    """FR-003: a fresh login session is created each time — this is what makes
    'human calibration once per login session' well-defined."""
    session = LoginSession(user_id=user.id)
    db.add(session)
    db.commit()
    db.refresh(session)

    token = create_access_token({"sub": user.id, "session_id": session.id})
    return TokenResponse(access_token=token, session_id=session.id)
