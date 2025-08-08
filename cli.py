from datetime import datetime, date
import argparse
import requests
from sqlalchemy.orm import Session
from wcwidth import wcswidth

from app.db import engine, Base
from app.models import VPS
from app.utils import calculate_remaining

Base.metadata.create_all(bind=engine)

RATE_API = "https://open.er-api.com/v6/latest/"

CYCLE_CHOICES = {
    "1": ("Monthly", 30),
    "2": ("Quarterly", 90),
    "3": ("Yearly", 365),
    "4": ("Three Years", 365 * 3),
}

def fetch_rate(currency: str) -> float:
    """Fetch exchange rate for currency to CNY."""
    try:
        resp = requests.get(f"{RATE_API}{currency}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("rates", {}).get("CNY", 1.0))
    except Exception:
        return 1.0

def prompt_date(prompt: str, default: date | None = None) -> date:
    while True:
        raw = input(prompt)
        if not raw and default:
            return default
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            print("Enter date as YYYY-MM-DD")

def choose_cycle() -> int:
    print("Choose payment cycle:")
    for key, (label, _) in CYCLE_CHOICES.items():
        print(f"{key}. {label}")
    choice = input("> ").strip()
    return CYCLE_CHOICES.get(choice, CYCLE_CHOICES["1"])[1]

def add_vps():
    name = input("VPS name: ").strip()
    currency = input("Currency (e.g., USD, CNY, EUR): ").strip().upper() or "USD"
    price = float(input("Renewal price: ").strip())
    cycle_days = choose_cycle()
    purchase_date = prompt_date("Purchase date (YYYY-MM-DD, default today): ", date.today())
    rate = fetch_rate(currency)
    with Session(engine) as db:
        vps = VPS(
            name=name,
            purchase_date=purchase_date,
            renewal_days=cycle_days,
            renewal_price=price,
            currency=currency,
            exchange_rate=rate,
        )
        db.add(vps)
        db.commit()
    print("VPS added.")

def list_vps():
    with Session(engine) as db:
        vps_list = db.query(VPS).all()
    if not vps_list:
        print("No VPS entries found.")
        return
    def pad(value: str, width: int, align: str = "left") -> str:
        """Pad ``value`` accounting for wide characters."""
        text = str(value)
        padding = width - wcswidth(text)
        if padding <= 0:
            return text
        if align == "right":
            return " " * padding + text
        return text + " " * padding

    header = (
        f"{pad('Name',15)} {pad('Currency',8)} "
        f"{pad('Price',10,'right')} {pad('Remain(d)',10,'right')} {pad('Value(CNY)',12,'right')}"
    )
    print(header)
    for vps in vps_list:
        data = calculate_remaining(vps)
        price_str = f"{vps.renewal_price:.2f}"
        remain_value_str = f"{data['remaining_value']:.2f}"
        line = (
            f"{pad(vps.name,15)} {pad(vps.currency,8)} "
            f"{pad(price_str,10,'right')} "
            f"{pad(data['remaining_days'],10,'right')} "
            f"{pad(remain_value_str,12,'right')}"
        )
        print(line)

def interactive_menu():
    while True:
        print("\n1. List VPS\n2. Add VPS\n3. Quit")
        choice = input("> ").strip()
        if choice == "1":
            list_vps()
        elif choice == "2":
            add_vps()
        elif choice == "3":
            break
        else:
            print("Invalid choice")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", nargs="?", choices=["list", "add"])
    args = parser.parse_args()
    if args.action == "list":
        list_vps()
    elif args.action == "add":
        add_vps()
    else:
        interactive_menu()

if __name__ == "__main__":
    main()
