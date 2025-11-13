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


def test_ping_ip_with_ipv6_without_port(monkeypatch):
    _ping_cache.clear()

    connections = []
    ping_calls = []

    def fake_create_connection(address, timeout=None):
        connections.append((address, timeout))

        class Dummy:
            def close(self):
                pass

        return Dummy()

    def fake_run(*args, **kwargs):
        ping_calls.append(args[0])

        class DummyCompleted:
            def __init__(self, returncode):
                self.returncode = returncode

        return DummyCompleted(returncode=1)

    monkeypatch.setattr("socket.create_connection", fake_create_connection)
    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.which", lambda _: "/bin/ping")

    status = ping_ip("::1")

    assert status == "🟢 在线"
    assert ping_calls, "Ping should be attempted for bare IPv6 addresses"
    assert connections == [(('::1', 80), 1)], "Bare IPv6 should fall back to port 80 only"


def test_ping_ip_with_bracketed_ipv6_and_port(monkeypatch):
    _ping_cache.clear()

    connections = []
    ping_calls = []

    def fake_create_connection(address, timeout=None):
        connections.append((address, timeout))

        class Dummy:
            def close(self):
                pass

        return Dummy()

    def fake_run(*args, **kwargs):
        ping_calls.append(args[0])

        class DummyCompleted:
            def __init__(self, returncode):
                self.returncode = returncode

        return DummyCompleted(returncode=0)

    monkeypatch.setattr("socket.create_connection", fake_create_connection)
    monkeypatch.setattr("subprocess.run", fake_run)

    status = ping_ip("[::1]:443")

    assert status == "🟢 在线"
    assert connections == [(('::1', 443), 1)]
    assert not ping_calls, "Bracketed IPv6 with port should skip ping"

