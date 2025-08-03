from app.utils import parse_instance_config


def test_parse_instance_config_formats():
    expected = {"cpu": "8C", "memory": "0.5G", "storage": "41G"}
    configs = ["8C/0.5G/41G", "8C 0.5G 41G", "8C|0.5G|41G"]
    for cfg in configs:
        assert parse_instance_config(cfg) == expected
