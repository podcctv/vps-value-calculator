import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("app_main", ROOT / "app.py")
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
mask_ip = app_module.mask_ip


def test_mask_ip_masks_last_two_octets():
    assert mask_ip("192.168.10.1") == "192.168.**.**"


def test_mask_ip_strips_port_before_masking():
    assert mask_ip("10.0.0.1:8080") == "10.0.**.**"


def test_mask_ip_without_ipv4_falls_back_to_host():
    assert mask_ip("example.com:1234") == "example.com"
