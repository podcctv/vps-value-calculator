from datetime import date
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static" / "images"

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def calculate_remaining(vps):
    today = date.today()
    if not vps.expiry_date or not vps.transaction_date:
        return {
            "remaining_days": 0,
            "remaining_value": 0.0,
            "cycle_end": vps.expiry_date,
        }
    remaining_days = max((vps.expiry_date - today).days, 0)
    total_days = max((vps.expiry_date - vps.transaction_date).days, 1)
    remaining_value = vps.renewal_price * vps.exchange_rate * remaining_days / total_days
    return {
        "remaining_days": remaining_days,
        "remaining_value": round(remaining_value, 2),
        "cycle_end": vps.expiry_date,
    }


def generate_svg(vps, data):
    template = env.get_template("vps.svg")
    content = template.render(vps=vps, data=data)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    out_file = STATIC_DIR / f"{vps.name}.svg"
    out_file.write_text(content, encoding="utf-8")
    return out_file
