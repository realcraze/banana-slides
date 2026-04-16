"""Microsoft profile metadata helpers."""

from __future__ import annotations

import base64
import json
import logging
import time
from typing import Optional

import requests
from flask import request

logger = logging.getLogger(__name__)

GRAPH_ME_URL = "https://graph.microsoft.com/v1.0/me"
_display_name_cache: dict[str, tuple[str, float]] = {}


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
        display_name = _profile_name_from_graph(_access_token_from_request())
    except Exception as exc:
        logger.warning("Failed to fetch Microsoft display name for %s: %s", email or fallback_name, exc)

    display_name = _first_non_empty(display_name, _profile_name_from_id_token(_id_token_from_request()), email)

    if display_name:
        _display_name_cache[cache_key] = (display_name, time.time() + 3600)
        return display_name

    return fallback_name
