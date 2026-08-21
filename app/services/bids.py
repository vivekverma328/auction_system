import logging

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session

from app.models.bids import Bid
from app.repositories.users import get_users_by_ids_for_update
from app.schemas.bids import BidCreate
from app.repositories.auctions import (
    get_auction_by_id,
    get_auction_by_id_for_update
)

from app.repositories.bids import (
    create_bid,
    get_bids_by_auction
)


def register_bid(
    db: Session,
    bidder_id: int,
    bid_data: BidCreate
):
    try:
        # Lock auction so bids on the same auction are serialized.
        auction = get_auction_by_id_for_update(
            db,
            bid_data.auction_id
        )

        if auction is None:
            raise ValueError("Auction does not exist")

        if auction.status != "ACTIVE":
            raise ValueError(
                "Bids can only be placed on ACTIVE auctions"
            )

        if auction.seller_id == bidder_id:
            raise ValueError(
                "Seller cannot bid on their own auction"
            )

        if bid_data.amount <= auction.current_highest_bid:
            raise ValueError(
                "Bid amount must be greater than "
                "the current highest bid"
            )

        previous_bidder_id = auction.current_highest_bidder_id

        user_ids_to_lock = [bidder_id]

        if (
            previous_bidder_id is not None
            and previous_bidder_id != bidder_id
        ):
            user_ids_to_lock.append(previous_bidder_id)

        users = get_users_by_ids_for_update(
            db,
            user_ids_to_lock
        )

        users_by_id = {
            user.id: user
            for user in users
        }

        bidder = users_by_id.get(bidder_id)

        if bidder is None:
            raise ValueError("Bidder does not exist")

        # ---------------------------------
        # Same highest bidder raises bid
        # ---------------------------------

        if previous_bidder_id == bidder_id:
            available_balance = (
                bidder.account_balance
                + auction.current_highest_bid
            )

            if available_balance < bid_data.amount:
                raise ValueError(
                    "Insufficient account balance"
                )

            bidder.account_balance = (
                available_balance
                - bid_data.amount
            )

        # ---------------------------------
        # New user becomes highest bidder
        # ---------------------------------

        else:
            if bidder.account_balance < bid_data.amount:
                raise ValueError(
                    "Insufficient account balance"
                )

            bidder.account_balance -= bid_data.amount

            if previous_bidder_id is not None:
                previous_bidder = users_by_id.get(
                    previous_bidder_id
                )

                if previous_bidder is None:
                    raise ValueError(
                        "Previous highest bidder does not exist"
                    )

                previous_bidder.account_balance += (
                    auction.current_highest_bid
                )

        bid = Bid(
            auction_id=auction.id,
            bidder_id=bidder_id,
            amount=bid_data.amount
        )

        bid = create_bid(
            db,
            bid
        )

        auction.current_highest_bid = bid_data.amount
        auction.current_highest_bidder_id = bidder_id

        db.commit()
        db.refresh(bid)

        logger.info(
            "Bid %s accepted for auction %s "
            "by user %s for amount %s",
            bid.id,
            auction.id,
            bidder_id,
            bid.amount
        )

        return bid

    except Exception:
        db.rollback()
        raise

def fetch_auction_bids(
    db: Session,
    auction_id: int,
    limit: int,
    offset: int
):
    auction = get_auction_by_id(
        db,
        auction_id
    )

    if auction is None:
        raise ValueError("Auction does not exist")

    return get_bids_by_auction(
        db,
        auction_id,
        limit,
        offset
    )