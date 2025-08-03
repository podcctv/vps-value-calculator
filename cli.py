from datetime import datetime, date
import argparse
import requests
from sqlalchemy.orm import Session

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
    transaction_date = prompt_date("Transaction date (YYYY-MM-DD, default today): ", date.today())
    rate = fetch_rate(currency)
    with Session(engine) as db:
        vps = VPS(
            name=name,
            transaction_date=transaction_date,
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
    header = f"{'Name':15} {'Currency':8} {'Price':>10} {'Remain(d)':>10} {'Value(CNY)':>12}"
    print(header)
    for vps in vps_list:
        data = calculate_remaining(vps)
        line = f"{vps.name:15} {vps.currency:8} {vps.renewal_price:10.2f} {data['remaining_days']:10} {data['remaining_value']:12.2f}"
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
