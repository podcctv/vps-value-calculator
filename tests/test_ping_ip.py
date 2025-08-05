import socket

from app.utils import _ping_cache, ping_ip


def test_ping_ip_with_open_port():
    _ping_cache.clear()
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    port = s.getsockname()[1]
    try:
        status = ping_ip(f"127.0.0.1:{port}")
    finally:
        s.close()
    assert status == "🟢 在线"


def test_ping_ip_with_closed_port():
    _ping_cache.clear()
    status = ping_ip("127.0.0.1:1")
    assert status == "🔴 离线"

