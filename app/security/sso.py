"""OIDC / SSO authentication (Google, Azure AD, Okta)."""

from __future__ import annotations

import os
import secrets
from typing import Any
from urllib.parse import urlencode

import httpx

from app.platform.config_loader import get_platform_config
from app.security.auth import create_access_token

_pending_states: dict[str, bool] = {}


def get_sso_config() -> dict:
    cfg = get_platform_config()._load("auth.yaml")
    sso = cfg.get("sso", {})
    return {
        "enabled": sso.get("enabled", False) or bool(os.getenv("SSO_CLIENT_ID")),
        "provider_name": sso.get("provider_name", "SSO"),
        "client_id": os.getenv("SSO_CLIENT_ID") or sso.get("client_id", ""),
        "client_secret": os.getenv("SSO_CLIENT_SECRET") or sso.get("client_secret", ""),
        "discovery_url": os.getenv("SSO_DISCOVERY_URL") or sso.get("discovery_url", ""),
        "redirect_uri": os.getenv("SSO_REDIRECT_URI") or sso.get("redirect_uri", ""),
        "scopes": sso.get("scopes", ["openid", "email", "profile"]),
        "domain_role_map": sso.get("domain_role_map", {}),
        "default_sso_role": sso.get("default_sso_role", "Engineering"),
    }


async def _fetch_discovery(discovery_url: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(discovery_url)
        resp.raise_for_status()
        return resp.json()


def build_sso_login_url() -> tuple[str, str]:
    """Return (authorization_url, state)."""
    sso = get_sso_config()
    if not sso["enabled"] or not sso["discovery_url"] or not sso["client_id"]:
        raise ValueError("SSO is not configured. Set SSO_CLIENT_ID and SSO_DISCOVERY_URL.")

    import asyncio
    discovery = asyncio.get_event_loop().run_until_complete(_fetch_discovery(sso["discovery_url"]))
    auth_endpoint = discovery["authorization_endpoint"]

    state = secrets.token_urlsafe(32)
    _pending_states[state] = True

    params = {
        "client_id": sso["client_id"],
        "response_type": "code",
        "scope": " ".join(sso["scopes"]),
        "redirect_uri": sso["redirect_uri"],
        "state": state,
    }
    return f"{auth_endpoint}?{urlencode(params)}", state


async def build_sso_login_url_async() -> tuple[str, str]:
    sso = get_sso_config()
    if not sso["enabled"] or not sso["discovery_url"] or not sso["client_id"]:
        raise ValueError("SSO is not configured. Set SSO_CLIENT_ID and SSO_DISCOVERY_URL.")

    discovery = await _fetch_discovery(sso["discovery_url"])
    auth_endpoint = discovery["authorization_endpoint"]
    state = secrets.token_urlsafe(32)
    _pending_states[state] = True

    params = {
        "client_id": sso["client_id"],
        "response_type": "code",
        "scope": " ".join(sso["scopes"]),
        "redirect_uri": sso["redirect_uri"],
        "state": state,
    }
    return f"{auth_endpoint}?{urlencode(params)}", state


def _resolve_role_from_email(email: str, sso: dict) -> str:
    domain = email.split("@")[-1] if "@" in email else ""
    return sso.get("domain_role_map", {}).get(domain, sso.get("default_sso_role", "Engineering"))


async def handle_sso_callback(code: str, state: str) -> dict[str, Any]:
    if state not in _pending_states:
        raise ValueError("Invalid OAuth state")
    del _pending_states[state]

    sso = get_sso_config()
    discovery = await _fetch_discovery(sso["discovery_url"])

    async with httpx.AsyncClient(timeout=15) as client:
        token_resp = await client.post(
            discovery["token_endpoint"],
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": sso["redirect_uri"],
                "client_id": sso["client_id"],
                "client_secret": sso["client_secret"],
            },
        )
        token_resp.raise_for_status()
        tokens = token_resp.json()

        userinfo_resp = await client.get(
            discovery["userinfo_endpoint"],
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        userinfo_resp.raise_for_status()
        userinfo = userinfo_resp.json()

    email = userinfo.get("email", userinfo.get("preferred_username", "sso_user"))
    username = userinfo.get("name", email)
    role = _resolve_role_from_email(email, sso)
    user_id = userinfo.get("sub", email)

    access_token = create_access_token({
        "sub": user_id,
        "username": username,
        "role": role,
        "email": email,
        "auth_method": "sso",
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user_id,
        "username": username,
        "role": role,
        "email": email,
        "auth_method": "sso",
    }
