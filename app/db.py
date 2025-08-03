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


_run_migrations()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
