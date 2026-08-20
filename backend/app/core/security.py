from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
# Same bearer scheme but non-throwing, so routes can fall back to a query-string
# token for contexts where a browser won't attach an Authorization header
# (an <img>/<video> src or a plain download link).
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    FR-001/FR-002/FR-003 + Security Requirement: every authenticated endpoint
    must verify identity via a real session token, not a client-supplied ID.
    """
    payload = decode_token(token)
    user_id = payload.get("sub")
    session_id = payload.get("session_id")
    if user_id is None or session_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    # stash the current session id on the user object for convenience downstream
    user.current_session_id = session_id
    return user


def _user_from_raw_token(token: str, db: Session) -> User:
    payload = decode_token(token)
    user_id = payload.get("sub")
    session_id = payload.get("session_id")
    if user_id is None or session_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    user.current_session_id = session_id
    return user


def get_current_user_flexible(
    token_header: Optional[str] = Depends(oauth2_scheme_optional),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> User:
    """
    Same identity check as get_current_user, but also accepts the JWT as a
    `?token=` query parameter. Reserved for the couple of GET endpoints that
    are loaded directly by <img>/<video> src or a plain <a href download>
    rather than via fetch() — the browser won't attach a custom
    Authorization header for those, so there's no other way to authenticate
    them from a static element without proxying bytes through JS.
    """
    raw = token_header or token
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _user_from_raw_token(raw, db)
