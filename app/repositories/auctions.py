from sqlalchemy.orm import Session

from app.models.auctions import Auction

def create_auction(db: Session, auction: Auction):
    db.add(auction)
    db.commit()
    db.refresh(auction)

    return auction

def get_auction_by_id(db: Session, auction_id: int):
    return db.query(Auction).filter(Auction.id == auction_id).first()

def get_all_auctions(db: Session):
    return db.query(Auction).all()