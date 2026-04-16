"""Authentication controller."""

from flask import Blueprint

from auth import load_current_user
from services.avatar_service import get_or_fetch_avatar_url
from services.profile_service import get_microsoft_display_name
from utils import success_response


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/me', methods=['GET'])
def get_me():
    user = load_current_user()
    payload = user.to_dict()
    if user.authenticated:
        payload['name'] = get_microsoft_display_name(user.email, user.name)
    payload['avatar_url'] = get_or_fetch_avatar_url(user.email) if user.authenticated else None
    return success_response(payload)
