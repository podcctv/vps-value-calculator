from datetime import date, timedelta
from calendar import monthrange
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import re
import requests

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static" / "images"

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def add_months(dt: date, months: int) -> date:
    """Return a date with ``months`` added, keeping day if possible."""
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, monthrange(year, month)[1])
    return date(year, month, day)


def calculate_remaining(vps):
    today = date.today()
    if not vps.purchase_date or not vps.renewal_days:
        return {
            "remaining_days": 0,
            "remaining_value": 0.0,
            "total_value": 0.0,
            "cycle_start": None,
            "cycle_end": None,
        }

    months_map = {30: 1, 90: 3, 365: 12, 1095: 36}
    start = vps.purchase_date
    if vps.renewal_days in months_map:
        months = months_map[vps.renewal_days]
        while add_months(start, months) <= today:
            start = add_months(start, months)
        end = add_months(start, months)
    else:
        delta = timedelta(days=vps.renewal_days)
        while start + delta <= today:
            start += delta
        end = start + delta

    remaining_days = max((end - today).days, 0)
    total_days = max((end - start).days, 1)
    rate = vps.exchange_rate or 1.0
    if getattr(vps, "exchange_rate_source", "") == "system":
        try:
            resp = requests.get(
                f"https://open.er-api.com/v6/latest/{vps.currency}", timeout=10
            )
            data = resp.json()
            rate = data.get("rates", {}).get("CNY", rate)
        except Exception:
            pass
    remaining_value = vps.renewal_price * rate * remaining_days / total_days
    total_value = vps.renewal_price * rate
    return {
        "remaining_days": remaining_days,
        "remaining_value": round(remaining_value, 2),
        "total_value": round(total_value, 2),
        "cycle_start": start,
        "cycle_end": end,
    }


def parse_instance_config(config: str):
    """Parse instance configuration like '2C2G120G' or '8C/0.5G/41G' into cpu/memory/storage."""
    cpu = memory = storage = "-"
    if not config:
        return {"cpu": cpu, "memory": memory, "storage": storage}

    # Normalize and find all numbers followed by letters
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*([A-Za-z]+)", config)
    for value, unit in matches:
        unit = unit.lower()
        if unit.startswith("c") and cpu == "-":
            cpu = f"{value}C"
            continue

        unit_map = {
            "g": "G",
            "gb": "GB",
            "m": "M",
            "mb": "MB",
            "t": "T",
            "tb": "TB",
        }

        if unit in unit_map:
            pretty = unit_map[unit]
            if memory == "-":
                memory = f"{value}{pretty}"
            elif storage == "-":
                storage = f"{value}{pretty}"

    return {"cpu": cpu, "memory": memory, "storage": storage}


def mask_ip(ip: str) -> str:
    """Mask the middle two octets of an IPv4 address."""
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.**.**.{parts[3]}"
    return ip


_ping_cache = {}


def ping_ip(ip: str) -> str:
    """Ping IP with simple caching and return emoji status."""
    import subprocess
    import time
    import platform
    import socket
    import shutil

    now = time.time()
    cached = _ping_cache.get(ip)
    if cached and now - cached[0] < 60:
        return cached[1]

    status = "🔴 离线"
    ping_exec = shutil.which("ping")
    if ping_exec:
        system = platform.system().lower()
        count_arg = "-n" if system.startswith("win") else "-c"
        timeout_arg = "-w" if system.startswith("win") else "-W"
        try:
            res = subprocess.run(
                [ping_exec, count_arg, "1", timeout_arg, "1", ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if res.returncode == 0:
                status = "🟢 在线"
        except Exception:
            pass

    if status == "🔴 离线":
        try:
            socket.create_connection((ip, 80), timeout=1).close()
            status = "🟢 在线"
        except Exception:
            pass

    _ping_cache[ip] = (now, status)
    return status


def ip_to_flag(ip: str) -> str:
    """Return emoji flag for IP using ipapi.co.

    The input ``ip`` may contain stray emoji or comments. We extract the
    first IPv4 address before querying the API so that a stored value like
    "🏳️ 160.1.2.3" still resolves correctly.
    """
    try:
        import re

        match = re.search(r"(?:\d{1,3}\.){3}\d{1,3}", ip)
        if not match:
            return "🏳️"
        clean_ip = match.group(0)
        resp = requests.get(f"https://ipapi.co/{clean_ip}/country/", timeout=5)
        code = resp.text.strip().upper()
        if len(code) == 2 and code.isalpha():
            return chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397)
    except Exception:
        pass
    return "🏳️"


def generate_svg(vps, data, config=None):
    template = env.get_template("vps.svg")
    specs = parse_instance_config(vps.instance_config)
    today = date.today()
    ip_raw = getattr(vps, "ip_address", "") or ""
    ip_info = {
        "ip_display": mask_ip(ip_raw) if ip_raw else "-",
        "ping_status": ping_ip(ip_raw) if ip_raw else "未知",
        "flag": ip_to_flag(ip_raw) if ip_raw else "🏳️",
    }
    content = template.render(
        vps=vps,
        data=data,
        specs=specs,
        today=today,
        config=config,
        ip_info=ip_info,
    )
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    out_file = STATIC_DIR / f"{vps.name}.svg"
    out_file.write_text(content, encoding="utf-8")
    return out_file
