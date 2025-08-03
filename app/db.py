from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite:///{DATA_DIR / 'vps.db'}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


def _run_migrations():
    """Minimal schema migrations for existing databases."""
    inspector = inspect(engine)
    if "vps" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("vps")]
        if "transaction_date" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE vps ADD COLUMN transaction_date DATE"))
                # Infer the transaction date from expiry_date and renewal_days
                conn.execute(
                    text(
                        """
                        UPDATE vps
                        SET transaction_date = DATE(expiry_date, '-' || renewal_days || ' day')
                        WHERE expiry_date IS NOT NULL AND renewal_days IS NOT NULL
                        """
                    )
                )
        if "expiry_date" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE vps ADD COLUMN expiry_date DATE"))
                # Infer the expiry date from transaction_date and renewal_days
                conn.execute(
                    text(
                        """
                        UPDATE vps
                        SET expiry_date = DATE(transaction_date, '+' || renewal_days || ' day')
                        WHERE expiry_date IS NULL AND transaction_date IS NOT NULL AND renewal_days IS NOT NULL
                        """
                    )
                )

        # Add any new optional columns introduced after initial release
        optional_columns = {
            "vendor_name": "TEXT",
            "instance_config": "TEXT",
            "location": "TEXT",
            "description": "TEXT",
            "traffic_limit": "TEXT",
            "ip_address": "TEXT",
            "payment_method": "TEXT",
            "transaction_fee": "FLOAT DEFAULT 0.0",
            "exchange_rate_source": "TEXT",
            "update_cycle": "INTEGER DEFAULT 7",
            "dynamic_svg": "BOOLEAN DEFAULT 1",
            "status": "TEXT DEFAULT 'active'",
            "cycle_base_date": "DATE",
        }
        for column, definition in optional_columns.items():
            if column not in columns:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE vps ADD COLUMN {column} {definition}"))

    # Ensure new fields in site_config table are present
    if "site_config" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("site_config")]
        if "copyright" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE site_config ADD COLUMN copyright TEXT"))
        if "site_url" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE site_config ADD COLUMN site_url TEXT"))
                if "image_base_url" in columns:
                    conn.execute(
                        text("UPDATE site_config SET site_url = image_base_url"),
                    )
        if "username" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE site_config ADD COLUMN username TEXT"))
                if "noodseek_id" in columns:
                    conn.execute(
                        text("UPDATE site_config SET username = noodseek_id"),
                    )


_run_migrations()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
