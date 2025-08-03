import pytest
import importlib.util
from pathlib import Path
import sys
import uuid

# Load the Flask application from app.py despite the package name conflict
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("app_main", ROOT / "app.py")
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
flask_app = app_module.app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client


def test_add_vps_with_optional_fields(client):
    # Register a user to satisfy login_required decorator
    username = f"u_{uuid.uuid4().hex}"
    response = client.post('/register', data={'username': username, 'password': 'p', 'invite_code': 'Flanker'})
    assert response.status_code == 302

    vps_name = f"vps_{uuid.uuid4().hex}"
    data = {
        'name': vps_name,
        'transaction_date': '2024-01-01',
        'renewal_days': '',
        'renewal_price': '',
        'currency': 'USD',
        'exchange_rate': '',
        'dynamic_svg': 'on',
    }
    response = client.post('/vps/new', data=data)
    assert response.status_code == 302


def test_invite_code_required(client):
    # Register initial user with invite code (works whether or not users exist)
    username1 = f"u_{uuid.uuid4().hex}"
    res = client.post('/register', data={'username': username1, 'password': 'p', 'invite_code': 'Flanker'})
    assert res.status_code == 302

    # Attempt to register second user without invite code
    username2 = f"u_{uuid.uuid4().hex}"
    res = client.post('/register', data={'username': username2, 'password': 'p'})
    assert res.status_code == 400

    # Register second user with correct invite code
    res = client.post('/register', data={'username': username2, 'password': 'p', 'invite_code': 'Flanker'})
    assert res.status_code == 302
