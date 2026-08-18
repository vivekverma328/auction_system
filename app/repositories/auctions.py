from sqlalchemy.orm import Session

from app.models.auctions import Auction

def create_auction(db: Session, auction: Auction):
    db.add(auction)

    db.flush()

    return auction

def get_auction_by_id(db: Session, auction_id: int):
    return db.query(Auction).filter(Auction.id == auction_id).first()

def get_all_auctions(db: Session):
    return db.query(Auction).all()

def transition_auction_status(
    db: Session,
    auction_id: int,
    expected_status: str,
    new_status: str
):
    updated_rows = (
        db.query(Auction)
        .filter(
            Auction.id == auction_id,
            Auction.status == expected_status
        )
        .update(
            {"status":new_status},
            synchronize_session=False
        )
    )

    if updated_rows == 0:
        db.rollback()
        return None

    db.commit()

    return get_auction_by_id(db, auction_id)