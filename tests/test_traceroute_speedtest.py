import json
import subprocess
from unittest.mock import patch, MagicMock

from app.utils import traceroute_ip, run_speedtest


def test_traceroute_unavailable():
    with patch('shutil.which', return_value=None):
        assert traceroute_ip('1.1.1.1') == 'traceroute unavailable'


def test_traceroute_timeout():
    mock_run = MagicMock(side_effect=subprocess.TimeoutExpired(cmd='traceroute', timeout=1))
    with patch('shutil.which', return_value='/usr/bin/traceroute'), \
         patch('subprocess.run', mock_run):
        assert traceroute_ip('1.1.1.1', timeout=1) == 'Traceroute timed out'


def test_speedtest_not_installed():
    with patch('shutil.which', return_value=None):
        assert run_speedtest() == {'error': 'speedtest not installed'}


def test_speedtest_parse():
    sample = {
        'download': {'bandwidth': 12500000},
        'upload': {'bandwidth': 5000000},
        'ping': {'latency': 20.123, 'jitter': 1.5},
    }
    mock_proc = MagicMock(returncode=0, stdout=json.dumps(sample), stderr='')
    with patch('shutil.which', return_value='/usr/bin/speedtest'), \
         patch('subprocess.run', return_value=mock_proc):
        res = run_speedtest()
        assert res['download_mbps'] == round(12500000*8/1_000_000, 2)
        assert res['upload_mbps'] == round(5000000*8/1_000_000, 2)
        assert res['ping_ms'] == round(20.123, 2)
        assert res['jitter_ms'] == round(1.5, 2)
