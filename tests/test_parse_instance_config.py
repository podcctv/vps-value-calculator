from app.utils import parse_instance_config


def test_parse_instance_config_formats():
    expected = {"cpu": "8C", "memory": "0.5G", "storage": "41G"}
    configs = ["8C/0.5G/41G", "8C 0.5G 41G", "8C|0.5G|41G"]
    for cfg in configs:
        assert parse_instance_config(cfg) == expected


def test_parse_instance_config_various_units():
    cfg = "4C/512MB/1TB"
    expected = {"cpu": "4C", "memory": "512MB", "storage": "1TB"}
    assert parse_instance_config(cfg) == expected
