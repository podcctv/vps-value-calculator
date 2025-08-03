from sqlalchemy import Column, Integer, String, Float, Date
from .db import Base


class VPS(Base):
    __tablename__ = "vps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    purchase_date = Column(Date)
    renewal_days = Column(Integer)
    price = Column(Float)
    renewal_price = Column(Float)
    currency = Column(String, default="USD")
    exchange_rate = Column(Float, default=1.0)
