from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.models.base import Base

class Auction(Base):
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    starting_price = Column(Float)
    current_highest_bid = Column(Float)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)