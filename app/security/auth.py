"""JWT authentication and user session management."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.platform.config_loader import get_platform_config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer = HTTPBearer(auto_error=False)

_AUTH_CONFIG: dict | None = None


def _load_auth_config() -> dict:
    global _AUTH_CONFIG
    if _AUTH_CONFIG is None:
        cfg = get_platform_config()
        _AUTH_CONFIG = cfg._load("auth.yaml")
    return _AUTH_CONFIG


def reload_auth_config() -> None:
    global _AUTH_CONFIG
    _AUTH_CONFIG = None


def get_auth_settings() -> dict:
    return _load_auth_config().get("auth", {})


def is_auth_enabled() -> bool:
    return get_auth_settings().get("enabled", False)


def is_auth_required() -> bool:
    settings = get_auth_settings()
    return settings.get("enabled", False) and settings.get("required", False)


def _get_jwt_secret() -> str:
    import os
    return os.getenv("JWT_SECRET") or get_auth_settings().get("jwt_secret", "dev-secret")


def _get_expire_minutes() -> int:
    return int(get_auth_settings().get("jwt_expire_minutes", 60))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    cfg = _load_auth_config()
    demo_mode = get_auth_settings().get("demo_mode", True)

    for user in cfg.get("local_users", []):
        if user.get("username") != username:
            continue
        stored = user.get("password_hash") or user.get("password", "")
        if user.get("password_hash"):
            if verify_password(password, stored):
                return user
        elif demo_mode and password == stored:
            return user
    return None


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=_get_expire_minutes())
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _get_jwt_secret(), algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, _get_jwt_secret(), algorithms=["HS256"])


def get_user_from_token(token: str) -> dict[str, Any]:
    try:
        payload = decode_token(token)
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "role": payload.get("role"),
            "auth_method": payload.get("auth_method", "local"),
        }
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any] | None:
    if not is_auth_enabled():
        return None
    if not is_auth_required():
        if credentials is None:
            return None
    else:
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    if credentials is None:
        return None
    return get_user_from_token(credentials.credentials)


async def require_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any]:
    if not is_auth_enabled():
        raise HTTPException(status_code=400, detail="Auth is disabled")
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return get_user_from_token(credentials.credentials)
