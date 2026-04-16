"""Microsoft profile photo caching."""

from __future__ import annotations

import hashlib
import logging
import os
import time
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests
from flask import current_app, request

logger = logging.getLogger(__name__)

GRAPH_PHOTO_URL = "https://graph.microsoft.com/v1.0/me/photo/$value"
GRAPH_USER_PHOTO_URL = "https://graph.microsoft.com/v1.0/users/{user_id}/photo/$value"
GRAPH_TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
GRAPH_DEFAULT_SCOPE = "https://graph.microsoft.com/.default"
CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}
_app_token_cache: dict[str, float | str] = {"access_token": "", "expires_at": 0}


def _avatar_dir() -> Path:
    configured = current_app.config.get("AVATAR_STORAGE_DIR")
    if configured:
        return Path(configured)
    project_root = Path(current_app.config.get("PROJECT_ROOT") or Path(__file__).resolve().parents[2])
    return project_root / "frontend" / "public" / "avatars"


def _public_url(filename: str) -> str:
    public_path = (current_app.config.get("AVATAR_PUBLIC_PATH") or "/avatars").rstrip("/")
    return f"{public_path}/{filename}"


def _token_from_request() -> Optional[str]:
    token = (request.headers.get("X-Forwarded-Access-Token") or "").strip()
    if token:
        return token

    auth_header = (request.headers.get("Authorization") or "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return None


def _email_hash(email: str) -> str:
    return hashlib.sha256(email.lower().encode("utf-8")).hexdigest()[:32]


def _cached_avatar(email: str, max_age_seconds: int) -> Optional[str]:
    avatar_dir = _avatar_dir()
    prefix = _email_hash(email)
    now = time.time()
    for path in avatar_dir.glob(f"{prefix}.*"):
        if path.is_file() and now - path.stat().st_mtime <= max_age_seconds:
            return _public_url(path.name)
    return None


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


def _fetch_photo(email: str, token: str, *, app_token: bool) -> Optional[requests.Response]:
    if app_token:
        user_id = quote(email, safe="")
        url = GRAPH_USER_PHOTO_URL.format(user_id=user_id)
    else:
        url = GRAPH_PHOTO_URL

    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=8,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response


def _store_avatar(email: str, response: requests.Response) -> Optional[str]:
    content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
    extension = CONTENT_TYPE_EXTENSIONS.get(content_type)
    if not extension:
        logger.warning("Unsupported Microsoft avatar content type: %s", content_type)
        return None

    avatar_dir = _avatar_dir()
    avatar_dir.mkdir(parents=True, exist_ok=True)
    prefix = _email_hash(email)
    for old_path in avatar_dir.glob(f"{prefix}.*"):
        try:
            old_path.unlink()
        except OSError:
            logger.warning("Failed to remove stale avatar file: %s", old_path)

    filename = f"{prefix}{extension}"
    target = avatar_dir / filename
    temp = target.with_suffix(f"{target.suffix}.tmp")
    with open(temp, "wb") as file:
        file.write(response.content)
    os.replace(temp, target)
    return _public_url(filename)


def get_or_fetch_avatar_url(email: Optional[str]) -> Optional[str]:
    if not email:
        return None

    max_age_seconds = int(current_app.config.get("AVATAR_CACHE_SECONDS") or 86400)
    cached = _cached_avatar(email, max_age_seconds)
    if cached:
        return cached

    try:
        app_token = _get_graph_app_token()
        if app_token:
            try:
                response = _fetch_photo(email, app_token, app_token=True)
                return _store_avatar(email, response) if response else None
            except requests.HTTPError as exc:
                logger.warning("Failed to fetch Microsoft avatar with app token for %s: %s", email, exc)

        token = _token_from_request()
        if token:
            response = _fetch_photo(email, token, app_token=False)
            return _store_avatar(email, response) if response else None
    except Exception as exc:
        logger.warning("Failed to fetch Microsoft avatar for %s: %s", email, exc)

    return None
