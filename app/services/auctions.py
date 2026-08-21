import logging
logger = logging.getLogger(__name__)

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.auctions import Auction
from app.models.users import User

from app.schemas.auctions import AuctionCreate

from app.repositories.outbox import (
    create_outbox_event,
    mark_outbox_processed
)

from app.repositories.users import get_users_by_ids_for_update

from app.repositories.auctions import (
    create_auction,
    get_auction_by_id,
    get_all_auctions,
    transition_auction_status,
    get_auction_by_id_for_update
)

from app.redis.scheduler import (
    schedule_auction_start,
    schedule_auction_end
)



def register_auction(
    db: Session,
    user: User,
    auction_data: AuctionCreate
):
    now = datetime.now(timezone.utc)

    if auction_data.start_time <= now:
        raise ValueError(
            "Auction start time must be in future"
        )

    if auction_data.end_time <= auction_data.start_time:
        raise ValueError(
            "Auction end time must be after start time"
        )

    duration = (
        auction_data.end_time
        - auction_data.start_time
    )

    if duration < timedelta(minutes=5):
        raise ValueError(
            "Auction duration must be at least 5 minutes"
        )

    if duration > timedelta(weeks=1):
        raise ValueError(
            "Auction duration cannot exceed 7 days"
        )

    if auction_data.start_time > now + timedelta(days=30):
        raise ValueError(
            "Auction cannot be scheduled "
            "more than 30 days in advance"
        )

    auction = Auction(
        title=auction_data.title,
        description=auction_data.description,
        starting_price=auction_data.starting_price,
        current_highest_bid=auction_data.starting_price,
        start_time=auction_data.start_time,
        end_time=auction_data.end_time,
        status="SCHEDULED",
        seller_id=user.id
    )

    # ---------------------------------
    # PostgreSQL transaction
    # ---------------------------------

    try:
        auction = create_auction(
            db,
            auction
        )

        outbox_event = create_outbox_event(
            db,
            event_type="AUCTION_CREATED",
            auction_id=auction.id
        )

        # Auction + outbox are committed together.
        db.commit()
        db.refresh(auction)

    except Exception:
        db.rollback()
        raise

    # ---------------------------------
    # Immediate Redis scheduling
    # ---------------------------------

    try:
        schedule_auction_start(
            auction.id,
            auction.start_time
        )

        schedule_auction_end(
            auction.id,
            auction.end_time
        )

        mark_outbox_processed(
            db,
            outbox_event
        )

    except Exception:
        # The auction itself is already safely committed.
        #
        # Do NOT fail the auction creation request.
        # Leave the outbox event unprocessed so the
        # recovery worker can retry later.
        db.rollback()

        logger.exception(
            "Immediate Redis scheduling failed "
            "for auction %s; outbox recovery will retry",
            auction.id
        )

    logger.info(
        "Auction %s created with status SCHEDULED",
        auction.id
    )

    return auction


def get_auction(
    db: Session,
    auction_id: int
):
    return get_auction_by_id(
        db,
        auction_id
    )


def fetch_all_auctions(
    db: Session,
    limit: int,
    offset: int
):
    return get_all_auctions(
        db,
        limit,
        offset
    )


def activate_auction(
    db: Session,
    auction_id: int
):
    return transition_auction_status(
        db,
        auction_id,
        "SCHEDULED",
        "ACTIVE"
    )


def end_auction(
    db: Session,
    auction_id: int
):
    try:
        auction = get_auction_by_id_for_update(
            db,
            auction_id
        )

        if auction is None:
            return None

        if auction.status != "ACTIVE":
            return None

        if auction.current_highest_bidder_id is not None:
            users = get_users_by_ids_for_update(
                db,
                [auction.seller_id]
            )

            if not users:
                raise ValueError(
                    "Auction seller does not exist"
                )

            seller = users[0]

            seller.account_balance += (
                auction.current_highest_bid
            )

        auction.status = "ENDED"

        db.commit()
        db.refresh(auction)

        logger.info(
            "Auction %s settled and marked ENDED",
            auction.id
        )

        return auction

    except Exception:
        db.rollback()
        raise