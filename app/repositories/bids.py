from sqlalchemy.orm import Session

from app.models.bids import Bid


def create_bid(db: Session, bid: Bid):
    db.add(bid)
    db.flush()

    return bid


def get_bid_by_id(db: Session, bid_id: int):
    return (
        db.query(Bid)
        .filter(Bid.id == bid_id)
        .first()
    )


def get_bids_by_auction(
    db: Session,
    auction_id: int,
    limit: int,
    offset: int
):
    return (
        db.query(Bid)
        .filter(Bid.auction_id == auction_id)
        .order_by(Bid.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )