"""Authentication and authorization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
import hmac
from typing import Callable, Optional

from flask import current_app, g, request

from utils import forbidden, unauthorized


API_AUTH_EXEMPT_PATHS = {
    '/api/access-code/check',
    '/api/access-code/verify',
    '/api/auth/me',
}


@dataclass
class AuthUser:
    authenticated: bool
    role: str
    auth_mode: str
    email: Optional[str] = None
    name: Optional[str] = None
    auth_bypassed: bool = False

    @property
    def is_admin(self) -> bool:
        return self.role == 'admin'

    def to_dict(self) -> dict:
        return {
            'authenticated': self.authenticated,
            'role': self.role,
            'email': self.email,
            'name': self.name,
            'auth_mode': self.auth_mode,
            'auth_bypassed': self.auth_bypassed,
        }


def is_api_auth_exempt_path(path: str) -> bool:
    return path in API_AUTH_EXEMPT_PATHS


def _get_auth_mode() -> str:
    return (current_app.config.get('AUTH_MODE') or 'disabled').strip().lower()


def _get_access_code() -> str:
    return (current_app.config.get('ACCESS_CODE') or '').strip()


def _get_admin_emails() -> set[str]:
    raw = current_app.config.get('AUTH_ADMIN_EMAILS') or ''
    return {email.strip().lower() for email in raw.split(',') if email.strip()}


def _build_local_user(auth_mode: str) -> AuthUser:
    return AuthUser(
        authenticated=True,
        role='admin',
        auth_mode=auth_mode,
        name='Local User',
        auth_bypassed=(auth_mode == 'disabled'),
    )


def _resolve_proxy_header_user(auth_mode: str) -> AuthUser:
    email_header = current_app.config.get('AUTH_TRUSTED_EMAIL_HEADER') or 'X-Forwarded-Email'
    name_header = current_app.config.get('AUTH_TRUSTED_NAME_HEADER') or 'X-Forwarded-Name'
    allowed_domain = (current_app.config.get('AUTH_ALLOWED_EMAIL_DOMAIN') or '').strip().lower()
    fail_open = bool(current_app.config.get('AUTH_FAIL_OPEN'))

    raw_email = (request.headers.get(email_header) or '').strip()
    raw_name = (request.headers.get(name_header) or '').strip() or None

    if not raw_email:
        if fail_open:
            return AuthUser(
                authenticated=True,
                role='user',
                auth_mode=auth_mode,
                name='Proxy Bypass User',
                auth_bypassed=True,
            )
        return AuthUser(authenticated=False, role='user', auth_mode=auth_mode)

    email = raw_email.lower()
    if allowed_domain and not email.endswith(f'@{allowed_domain}'):
        return AuthUser(authenticated=False, role='user', auth_mode=auth_mode, email=email, name=raw_name)

    role = 'admin' if email in _get_admin_emails() else 'user'
    return AuthUser(
        authenticated=True,
        role=role,
        auth_mode=auth_mode,
        email=email,
        name=raw_name,
    )


def _resolve_access_code_user(auth_mode: str) -> AuthUser:
    expected = _get_access_code()
    if not expected:
        return _build_local_user(auth_mode)

    supplied = (request.headers.get('X-Access-Code') or '').strip()
    if supplied and hmac.compare_digest(supplied, expected):
        return AuthUser(
            authenticated=True,
            role='admin',
            auth_mode=auth_mode,
            name='Access Code User',
        )
    return AuthUser(authenticated=False, role='user', auth_mode=auth_mode)


def resolve_current_user() -> AuthUser:
    auth_mode = _get_auth_mode()
    if auth_mode == 'proxy_header':
        return _resolve_proxy_header_user(auth_mode)
    if auth_mode == 'access_code':
        return _resolve_access_code_user(auth_mode)
    return _build_local_user(auth_mode)


def load_current_user() -> AuthUser:
    user = resolve_current_user()
    g.current_user = user
    return user


def get_current_user() -> AuthUser:
    user = getattr(g, 'current_user', None)
    if user is None:
        user = load_current_user()
    return user


def require_authenticated(fn: Callable):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not get_current_user().authenticated:
            return unauthorized()
        return fn(*args, **kwargs)

    return wrapper


def require_admin(fn: Callable):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user.authenticated:
            return unauthorized()
        if not user.is_admin:
            return forbidden()
        return fn(*args, **kwargs)

    return wrapper


def can_access_project(user: AuthUser, project) -> bool:
    """Admins can access all projects; regular users only access their own."""
    if not user or not user.authenticated or project is None:
        return False
    if user.is_admin:
        return True

    user_email = (user.email or '').strip().lower()
    project_owner = (getattr(project, 'created_by_email', None) or '').strip().lower()
    return bool(user_email and project_owner and user_email == project_owner)
