from sqlalchemy import Column, Integer, String, Float, Date, Boolean
from .db import Base


class VPS(Base):
    __tablename__ = "vps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    transaction_date = Column(Date)
    expiry_date = Column(Date)
    renewal_days = Column(Integer)
    renewal_price = Column(Float)
    currency = Column(String, default="USD")
    exchange_rate = Column(Float, default=1.0)
    vendor_name = Column(String)
    instance_config = Column(String)
    location = Column(String)
    purpose = Column(String)
    traffic_limit = Column(String)
    payment_method = Column(String)
    transaction_fee = Column(Float, default=0.0)
    exchange_rate_source = Column(String, default="system")
    update_cycle = Column(Integer, default=7)
    dynamic_svg = Column(Boolean, default=True)
    status = Column(String, default="active")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_admin = Column(Boolean, default=False)
