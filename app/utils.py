from datetime import date, timedelta
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static" / "images"

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def calculate_remaining(vps):
    today = date.today()
    cycle_end = vps.purchase_date + timedelta(days=vps.renewal_days)
    remaining_days = max((cycle_end - today).days, 0)
    remaining_value = vps.price * remaining_days / vps.renewal_days
    return {
        "remaining_days": remaining_days,
        "remaining_value": round(remaining_value, 2),
        "cycle_end": cycle_end,
    }


def generate_svg(vps, data):
    template = env.get_template("vps.svg")
    content = template.render(vps=vps, data=data)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    out_file = STATIC_DIR / f"{vps.name}.svg"
    out_file.write_text(content, encoding="utf-8")
    return out_file
