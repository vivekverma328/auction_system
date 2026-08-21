from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from app.models.base import Base

class Auction(Base):
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    starting_price = Column(Numeric(12,2), nullable=False)
    current_highest_bid = Column(Numeric(12,2), nullable=False)
    current_highest_bidder_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)