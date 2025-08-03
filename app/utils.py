from datetime import date
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import re

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static" / "images"

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def calculate_remaining(vps):
    today = date.today()
    start_date = vps.cycle_base_date or vps.transaction_date
    if not vps.expiry_date or not start_date:
        return {
            "remaining_days": 0,
            "remaining_value": 0.0,
            "cycle_end": vps.expiry_date,
        }
    remaining_days = max((vps.expiry_date - today).days, 0)
    total_days = max((vps.expiry_date - start_date).days, 1)
    remaining_value = vps.renewal_price * vps.exchange_rate * remaining_days / total_days
    total_value = vps.renewal_price * vps.exchange_rate
    return {
        "remaining_days": remaining_days,
        "remaining_value": round(remaining_value, 2),
        "total_value": round(total_value, 2),
        "cycle_end": vps.expiry_date,
    }


def parse_instance_config(config: str):
    """Parse instance configuration like '2C2G120G' into cpu/memory/storage."""
    cpu = memory = storage = "-"
    if not config:
        return {"cpu": cpu, "memory": memory, "storage": storage}

    # Normalize and find all numbers followed by letters
    matches = re.findall(r"(\d+)\s*([A-Za-z]+)", config)
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


def generate_svg(vps, data):
    template = env.get_template("vps.svg")
    content = template.render(vps=vps, data=data)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    out_file = STATIC_DIR / f"{vps.name}.svg"
    out_file.write_text(content, encoding="utf-8")
    return out_file
