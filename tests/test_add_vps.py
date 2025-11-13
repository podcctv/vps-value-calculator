import pytest
import importlib.util
from pathlib import Path
import sys
import uuid
from urllib.parse import quote

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
        'purchase_date': '2024-01-01',
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


def test_manage_displays_ip_without_port(client):
    username = f"u_{uuid.uuid4().hex}"
    res = client.post('/register', data={'username': username, 'password': 'p', 'invite_code': 'Flanker'})
    assert res.status_code == 302

    vps_name = f"vps_{uuid.uuid4().hex}"
    data = {
        'name': vps_name,
        'purchase_date': '2024-01-01',
        'renewal_days': '',
        'renewal_price': '',
        'currency': 'USD',
        'exchange_rate': '',
        'dynamic_svg': 'on',
        'ip_address': '1.2.3.4:5678',
    }
    res = client.post('/vps/new', data=data)
    assert res.status_code == 302

    resp = client.get('/manage')
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert '1.**.**.4' in text
    assert ':5678' not in text


def test_svg_url_handles_special_chars(client):
    username = f"u_{uuid.uuid4().hex}"
    res = client.post('/register', data={'username': username, 'password': 'p', 'invite_code': 'Flanker'})
    assert res.status_code == 302

    vps_name = "[香港]" + uuid.uuid4().hex
    data = {
        'name': vps_name,
        'purchase_date': '2024-01-01',
        'renewal_days': '',
        'renewal_price': '',
        'currency': 'USD',
        'exchange_rate': '',
        'dynamic_svg': 'on',
    }
    res = client.post('/vps/new', data=data)
    assert res.status_code == 302

    encoded = quote(vps_name)
    resp = client.get(f'/vps/{encoded}.svg')
    assert resp.status_code == 200


def test_add_vps_rejects_path_traversal(client):
    username = f"u_{uuid.uuid4().hex}"
    res = client.post('/register', data={'username': username, 'password': 'p', 'invite_code': 'Flanker'})
    assert res.status_code == 302

    svg_files_before = {p.relative_to(ROOT) for p in ROOT.glob('static/**/*.svg')}
    data = {
        'name': '../etc/passwd',
        'purchase_date': '2024-01-01',
        'renewal_days': '',
        'renewal_price': '',
        'currency': 'USD',
        'exchange_rate': '',
        'dynamic_svg': 'on',
    }
    res = client.post('/vps/new', data=data)
    assert res.status_code == 400

    svg_files_after = {p.relative_to(ROOT) for p in ROOT.glob('static/**/*.svg')}
    assert svg_files_after == svg_files_before
    outside_path = ROOT / 'static' / 'etc' / 'passwd.svg'
    assert not outside_path.exists()
