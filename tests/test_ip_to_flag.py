from app.utils import ip_to_flag

class DummyResponse:
    def __init__(self, data):
        import json
        self._data = data
        self.text = json.dumps(data)
    def json(self):
        return self._data


def test_ip_to_flag_handles_json_response(monkeypatch):
    def fake_get(url, timeout=5):
        return DummyResponse({'countryCode': 'US'})
    monkeypatch.setattr('app.utils.requests.get', fake_get)
    assert ip_to_flag('8.8.8.8') == '\U0001F1FA\U0001F1F8'


def test_ip_to_flag_extracts_ipv4(monkeypatch):
    def fake_get(url, timeout=5):
        return DummyResponse({'countryCode': 'AU'})
    monkeypatch.setattr('app.utils.requests.get', fake_get)
    assert ip_to_flag('some text 🇺🇳 1.2.3.4') == '\U0001F1E6\U0001F1FA'
