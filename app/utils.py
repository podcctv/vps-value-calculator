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
        elif unit.startswith("g") and memory == "-":
            memory = f"{value}G"
        elif unit.startswith("g") and memory != "-" and storage == "-":
            storage = f"{value}G"
        elif unit.startswith("t") and storage == "-":
            storage = f"{value}T"

    return {"cpu": cpu, "memory": memory, "storage": storage}


def generate_svg(vps, data, config=None):
    template = env.get_template("vps.svg")
    specs = parse_instance_config(vps.instance_config)
    today = date.today()
    content = template.render(
        vps=vps,
        data=data,
        specs=specs,
        today=today,
        config=config,
    )
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    out_file = STATIC_DIR / f"{vps.name}.svg"
    out_file.write_text(content, encoding="utf-8")
    return out_file
