from models import Project, Settings, db


def _set_proxy_auth(app, admin_emails: str = 'admin@company.com'):
    app.config.update({
        'AUTH_MODE': 'proxy_header',
        'AUTH_ALLOWED_EMAIL_DOMAIN': 'company.com',
        'AUTH_TRUSTED_EMAIL_HEADER': 'X-Forwarded-Email',
        'AUTH_TRUSTED_NAME_HEADER': 'X-Forwarded-Name',
        'AUTH_ADMIN_EMAILS': admin_emails,
        'AUTH_FAIL_OPEN': False,
    })


def test_proxy_header_requires_authenticated_api_access(app, client):
    _set_proxy_auth(app)

    response = client.get('/api/projects')

    assert response.status_code == 401
    body = response.get_json()
    assert body['error']['code'] == 'AUTH_REQUIRED'


def test_auth_me_returns_admin_role_from_proxy_headers(app, client):
    _set_proxy_auth(app)

    response = client.get('/api/auth/me', headers={
        'X-Forwarded-Email': 'admin@company.com',
        'X-Forwarded-Name': 'Admin User',
    })

    assert response.status_code == 200
    body = response.get_json()['data']
    assert body['authenticated'] is True
    assert body['role'] == 'admin'
    assert body['email'] == 'admin@company.com'
    assert body['name'] == 'Admin User'


def test_proxy_header_rejects_non_company_email(app, client):
    _set_proxy_auth(app)

    me = client.get('/api/auth/me', headers={'X-Forwarded-Email': 'user@gmail.com'})
    assert me.status_code == 200
    assert me.get_json()['data']['authenticated'] is False

    projects = client.get('/api/projects', headers={'X-Forwarded-Email': 'user@gmail.com'})
    assert projects.status_code == 401


def test_non_admin_cannot_access_settings(app, client):
    _set_proxy_auth(app)

    response = client.get('/api/settings/', headers={'X-Forwarded-Email': 'user@company.com'})

    assert response.status_code == 403
    body = response.get_json()
    assert body['error']['code'] == 'FORBIDDEN'


def test_public_settings_remain_available_to_authenticated_users(app, client):
    _set_proxy_auth(app)
    with app.app_context():
        settings = Settings.get_settings()
        settings.image_resolution = '1K'
        settings.api_key = 'super-secret-key'
        db.session.commit()

    response = client.get('/api/settings/public', headers={'X-Forwarded-Email': 'user@company.com'})

    assert response.status_code == 200
    body = response.get_json()['data']
    assert body['image_resolution'] == '1K'
    assert 'api_key' not in body


def test_admin_can_get_settings_without_plaintext_secrets(app, client):
    _set_proxy_auth(app)
    with app.app_context():
        settings = Settings.get_settings()
        settings.api_key = 'super-secret-key'
        settings.mineru_token = 'mineru-secret'
        db.session.commit()

    response = client.get('/api/settings/', headers={'X-Forwarded-Email': 'admin@company.com'})

    assert response.status_code == 200
    body = response.get_json()['data']
    assert body['api_key_length'] == len('super-secret-key')
    assert body['mineru_token_length'] == len('mineru-secret')
    assert 'api_key' not in body
    assert 'mineru_token' not in body


def test_create_project_records_creator_email(app, client):
    _set_proxy_auth(app)

    response = client.post('/api/projects', json={
        'creation_type': 'idea',
        'idea_prompt': 'Security rollout',
    }, headers={'X-Forwarded-Email': 'user@company.com'})

    assert response.status_code == 201
    project_id = response.get_json()['data']['project_id']

    with app.app_context():
        project = Project.query.get(project_id)
        assert project is not None
        assert project.created_by_email == 'user@company.com'
