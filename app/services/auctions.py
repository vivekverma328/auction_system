from sqlalchemy.orm import Session
from app.models.auctions import Auction
from app.models.users import User
from app.schemas.auctions import AuctionCreate
from app.repositories.auctions import create_auction, get_auction_by_id, get_all_auctions

from datetime import datetime, timedelta, timezone

def register_auction(db: Session, user: User, auction_data: AuctionCreate):
    now = datetime.now(timezone.utc)

    if auction_data.start_time <= now:
        raise ValueError("Auction start time must be in future")

    if auction_data.end_time <= auction_data.start_time:
        raise ValueError("Auction end time must be after start time")

    duration = auction_data.end_time - auction_data.start_time

    if duration < timedelta(minutes=5):
        raise ValueError("Auction duration must be at least 5 minutes")

    if duration > timedelta(weeks=1):
        raise ValueError("Auction duration cannot exceed 7 days")

    if auction_data.start_time > now + timedelta(days=30):
        raise ValueError("Auction cannot be scheduled more than 30 days in advance")
    
    auction = Auction(
        title = auction_data.title,
        description = auction_data.description,
        starting_price = auction_data.starting_price,
        current_highest_bid = auction_data.starting_price,
        start_time = auction_data.start_time,
        end_time = auction_data.end_time,
        status = "SCHEDULED",
        seller_id = user.id
    )

    return create_auction(db, auction)

def get_auction(db: Session, auction_id: int):
    return get_auction_by_id(db, auction_id)

def fetch_all_auctions(db: Session):
    return get_all_auctions(db)