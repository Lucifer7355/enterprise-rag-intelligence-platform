"""Authentication and SSO routes."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.security.auth import (
    authenticate_user,
    create_access_token,
    get_auth_settings,
    is_auth_enabled,
    reload_auth_config,
)
from app.security.sso import build_sso_login_url_async, get_sso_config, handle_sso_callback

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str
    auth_method: str = "local"


class AuthStatusResponse(BaseModel):
    auth_enabled: bool
    sso_enabled: bool
    demo_users: list[str]


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status():
    from app.platform.config_loader import get_platform_config
    cfg = get_platform_config()._load("auth.yaml")
    users = [u.get("username", "") for u in cfg.get("local_users", [])]
    sso = get_sso_config()
    return AuthStatusResponse(
        auth_enabled=is_auth_enabled(),
        sso_enabled=sso.get("enabled", False),
        demo_users=users,
    )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    if not is_auth_enabled():
        raise HTTPException(status_code=400, detail="Authentication is disabled")

    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({
        "sub": user.get("user_id", user["username"]),
        "username": user["username"],
        "role": user["role"],
        "auth_method": "local",
    })

    return LoginResponse(
        access_token=token,
        user_id=user.get("user_id", user["username"]),
        username=user["username"],
        role=user["role"],
    )


@router.get("/sso/login")
async def sso_login():
    try:
        url, _ = await build_sso_login_url_async()
        return RedirectResponse(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/sso/callback")
async def sso_callback(code: str = Query(...), state: str = Query(...)):
    try:
        result = await handle_sso_callback(code, state)
        ui_url = f"http://localhost:8501/?token={result['access_token']}&role={result['role']}&user={result['username']}"
        return RedirectResponse(ui_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SSO failed: {e}") from e


@router.post("/reload")
async def reload_auth():
    reload_auth_config()
    return {"status": "auth config reloaded"}
