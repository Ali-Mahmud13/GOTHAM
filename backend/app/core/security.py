"""JWT auth, legacy header shim, and patient access checks."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Annotated, Callable

import jwt
from fastapi import Depends, Header, HTTPException, status
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.core import config
from app.db.session import get_session
from app.models.auth import AuthUser

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def is_legacy_sha256_hash(stored: str) -> bool:
    return len(stored) == 64 and all(c in "0123456789abcdef" for c in stored.lower())


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_stored_password(plain: str, stored: str) -> bool:
    if stored.startswith("$2") or stored.startswith("$pb"):
        try:
            return pwd_context.verify(plain, stored)
        except Exception:
            return False
    if config.ALLOW_LEGACY_PASSWORD_HASH and is_legacy_sha256_hash(stored):
        return hashlib.sha256(plain.encode()).hexdigest() == stored.lower()
    return False


def create_access_token(*, user_id: int, email: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=config.JWT_ACCESS_MINUTES)
    return jwt.encode(
        {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "typ": "access",
            "iat": now,
            "exp": exp,
        },
        config.JWT_SECRET,
        algorithm="HS256",
    )


def create_refresh_token(*, user_id: int, email: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=config.JWT_REFRESH_DAYS)
    return jwt.encode(
        {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "typ": "refresh",
            "iat": now,
            "exp": exp,
        },
        config.JWT_SECRET,
        algorithm="HS256",
    )


def _decode_token(token: str, expected_typ: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET,
            algorithms=["HS256"],
            options={"require": ["sub", "exp"]},
        )
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        ) from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from e
    if payload.get("typ") != expected_typ:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")
    return payload


def decode_access_token(token: str) -> dict:
    return _decode_token(token, "access")


def decode_refresh_token(token: str) -> dict:
    return _decode_token(token, "refresh")


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    session: Session = Depends(get_session),
) -> AuthUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(token)
    uid = int(payload["sub"])
    user = session.get(AuthUser, uid)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_user_compat(
    authorization: Annotated[str | None, Header()] = None,
    x_user_email: Annotated[str | None, Header(alias="X-User-Email")] = None,
    session: Session = Depends(get_session),
) -> AuthUser:
    if authorization and authorization.lower().startswith("bearer "):
        return get_current_user(authorization=authorization, session=session)
    if config.ALLOW_LEGACY_HEADER_AUTH and x_user_email:
        logger.warning("Authenticated via legacy X-User-Email header; use Authorization: Bearer")
        user = session.exec(select(AuthUser).where(AuthUser.email == x_user_email.lower())).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def require_role(*roles: str) -> Callable[..., AuthUser]:
    def _dep(user: AuthUser = Depends(get_current_user_compat)) -> AuthUser:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _dep


def require_admin(user: AuthUser = Depends(get_current_user_compat)) -> AuthUser:
    if not getattr(user, "is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user


if TYPE_CHECKING:
    from app.models.patient import Patient


def assert_patient_access(user: AuthUser, patient: "Patient") -> None:
    """Patient may access own record; doctor only assigned patients."""
    if user.role == "patient":
        if user.patient_id != patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You may only access your own patient record",
            )
    elif user.role == "doctor":
        if patient.doctor_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You may only access patients registered with you",
            )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
