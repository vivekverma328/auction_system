from sqlalchemy import Column, Integer, String, Numeric
from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    account_balance = Column(Numeric(12,2), nullable=False, default=0)