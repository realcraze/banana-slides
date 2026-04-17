"""Microsoft profile metadata helpers."""

from __future__ import annotations

import base64
import json
import logging
import time
from typing import Optional
from urllib.parse import quote

import requests
from flask import current_app, request

logger = logging.getLogger(__name__)

GRAPH_ME_URL = "https://graph.microsoft.com/v1.0/me"
GRAPH_USER_URL = "https://graph.microsoft.com/v1.0/users/{user_id}"
GRAPH_TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
GRAPH_DEFAULT_SCOPE = "https://graph.microsoft.com/.default"
_display_name_cache: dict[str, tuple[str, float]] = {}
_app_token_cache: dict[str, float | str] = {"access_token": "", "expires_at": 0}


def _access_token_from_request() -> Optional[str]:
    token = (request.headers.get("X-Forwarded-Access-Token") or "").strip()
    if token:
        return token

    return None


def _id_token_from_request() -> Optional[str]:
    auth_header = (request.headers.get("Authorization") or "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return None


def _decode_unverified_jwt_payload(token: Optional[str]) -> dict:
    if not token:
        return {}

    parts = token.split(".")
    if len(parts) < 2:
        return {}

    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(payload.encode("utf-8")))
    except Exception:
        return {}


def _first_non_empty(*values: Optional[str]) -> Optional[str]:
    for value in values:
        trimmed = (value or "").strip()
        if trimmed:
            return trimmed
    return None


def _usable_display_name(value: Optional[str], email: Optional[str]) -> Optional[str]:
    trimmed = (value or "").strip()
    if not trimmed or "@" in trimmed:
        return None

    email_local = (email or "").split("@")[0].strip().lower()
    if email_local and trimmed.lower() == email_local:
        return None

    return trimmed


def _get_graph_app_token() -> Optional[str]:
    cached_token = str(_app_token_cache.get("access_token") or "")
    expires_at = float(_app_token_cache.get("expires_at") or 0)
    if cached_token and time.time() < expires_at - 60:
        return cached_token

    tenant_id = current_app.config.get("ENTRA_TENANT_ID")
    client_id = current_app.config.get("ENTRA_CLIENT_ID")
    client_secret = current_app.config.get("ENTRA_CLIENT_SECRET")
    if not tenant_id or not client_id or not client_secret:
        return None

    response = requests.post(
        GRAPH_TOKEN_URL.format(tenant_id=tenant_id),
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": GRAPH_DEFAULT_SCOPE,
        },
        timeout=8,
    )
    response.raise_for_status()
    payload = response.json()
    access_token = payload.get("access_token")
    if not access_token:
        return None

    _app_token_cache["access_token"] = access_token
    _app_token_cache["expires_at"] = time.time() + int(payload.get("expires_in") or 3600)
    return access_token


def _profile_name_from_graph_app(email: Optional[str]) -> Optional[str]:
    if not email:
        return None

    app_token = _get_graph_app_token()
    if not app_token:
        return None

    response = requests.get(
        GRAPH_USER_URL.format(user_id=quote(email, safe="")),
        params={"$select": "displayName,mail,userPrincipalName"},
        headers={"Authorization": f"Bearer {app_token}"},
        timeout=8,
    )
    response.raise_for_status()
    profile = response.json()
    return _first_non_empty(profile.get("displayName"), profile.get("name"))


def _profile_name_from_graph(access_token: Optional[str]) -> Optional[str]:
    if not access_token:
        return None

    response = requests.get(
        GRAPH_ME_URL,
        params={"$select": "displayName,mail,userPrincipalName"},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=8,
    )
    response.raise_for_status()
    profile = response.json()
    return _first_non_empty(profile.get("name"), profile.get("displayName"))


def _profile_name_from_id_token(id_token: Optional[str]) -> Optional[str]:
    payload = _decode_unverified_jwt_payload(id_token)
    return _first_non_empty(payload.get("name"))


def get_microsoft_display_name(email: Optional[str], fallback_name: Optional[str]) -> Optional[str]:
    """Return the user's Microsoft display name when available.

    Mirrors the app-owned OAuth flow used by the reference project:
    profile.name -> profile.displayName -> token.name -> email.
    oauth2-proxy's X-Forwarded-User is only a final fallback because it is often
    an account id such as "bo.gao".
    """
    if not email and not fallback_name:
        return None

    cache_key = (email or fallback_name or "").lower()
    cached = _display_name_cache.get(cache_key)
    if cached and time.time() < cached[1]:
        return cached[0]

    display_name = None
    try:
        display_name = _profile_name_from_graph_app(email)
    except Exception as exc:
        logger.warning("Failed to fetch Microsoft display name with app token for %s: %s", email or fallback_name, exc)

    try:
        display_name = display_name or _profile_name_from_graph(_access_token_from_request())
    except Exception as exc:
        logger.warning("Failed to fetch Microsoft display name for %s: %s", email or fallback_name, exc)

    display_name = _first_non_empty(
        display_name,
        _profile_name_from_id_token(_id_token_from_request()),
        _usable_display_name(fallback_name, email),
        email,
    )

    if display_name:
        _display_name_cache[cache_key] = (display_name, time.time() + 3600)
        return display_name

    return fallback_name
