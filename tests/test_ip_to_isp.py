from app.utils import ip_to_isp, _isp_cache

class DummyResponse:
    def __init__(self, data):
        import json
        self._data = data
        self.text = json.dumps(data)
    def json(self):
        return self._data

def test_ip_to_isp_handles_json_response(monkeypatch):
    _isp_cache.clear()
    def fake_get(url, timeout=5):
        return DummyResponse({'isp': 'ExampleISP'})
    monkeypatch.setattr('app.utils.requests.get', fake_get)
    assert ip_to_isp('8.8.8.8') == 'ExampleISP'

def test_ip_to_isp_extracts_ipv4(monkeypatch):
    _isp_cache.clear()
    def fake_get(url, timeout=5):
        return DummyResponse({'isp': 'AnotherISP'})
    monkeypatch.setattr('app.utils.requests.get', fake_get)
    assert ip_to_isp('random text 1.2.3.4') == 'AnotherISP'
