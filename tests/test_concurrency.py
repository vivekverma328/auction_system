from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from app.database import SessionLocal
from app.models.auctions import Auction
from app.models.users import User
from app.schemas.bids import BidCreate
from app.services.bids import register_bid


def place_bid(
    auction_id: int,
    bidder_id: int,
    amount: Decimal,
    barrier: Barrier
):
    db = SessionLocal()

    try:
        # Force both threads to reach the bid operation
        # at approximately the same time.
        barrier.wait()

        bid = register_bid(
            db,
            bidder_id,
            BidCreate(
                auction_id=auction_id,
                amount=amount
            )
        )

        return "success", bid.amount

    except ValueError as exc:
        return "rejected", str(exc)

    finally:
        db.close()


def test_concurrent_bids_keep_highest_bid_consistent(
    client,
    user_factory,
    token_factory,
    add_balance,
    auction_factory,
    activate_auction
):
    user_factory(
        "Seller",
        "seller@example.com"
    )

    seller_token = token_factory(
        "seller@example.com"
    )

    auction = auction_factory(
        seller_token,
        Decimal("1000.00")
    )

    activate_auction(
        auction["id"]
    )

    bidder_one = user_factory(
        "Bidder One",
        "bidder1@example.com"
    )

    bidder_two = user_factory(
        "Bidder Two",
        "bidder2@example.com"
    )

    token_one = token_factory(
        "bidder1@example.com"
    )

    token_two = token_factory(
        "bidder2@example.com"
    )

    add_balance(
        token_one,
        Decimal("10000.00")
    )

    add_balance(
        token_two,
        Decimal("10000.00")
    )

    barrier = Barrier(2)

    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:
        future_one = executor.submit(
            place_bid,
            auction["id"],
            bidder_one["id"],
            Decimal("1200.00"),
            barrier
        )

        future_two = executor.submit(
            place_bid,
            auction["id"],
            bidder_two["id"],
            Decimal("1500.00"),
            barrier
        )

        result_one = future_one.result()
        result_two = future_two.result()

    db = SessionLocal()

    try:
        auction_row = (
            db.query(Auction)
            .filter(
                Auction.id == auction["id"]
            )
            .first()
        )

        bidder_one_row = (
            db.query(User)
            .filter(
                User.id == bidder_one["id"]
            )
            .first()
        )

        bidder_two_row = (
            db.query(User)
            .filter(
                User.id == bidder_two["id"]
            )
            .first()
        )

        assert auction_row.current_highest_bid == Decimal(
            "1500.00"
        )

        assert (
            auction_row.current_highest_bidder_id
            == bidder_two["id"]
        )

        # Bidder one either:
        # 1. bid first and was refunded, or
        # 2. bid second and was rejected.
        #
        # In either case their final balance is unchanged.
        assert bidder_one_row.account_balance == Decimal(
            "10000.00"
        )

        assert bidder_two_row.account_balance == Decimal(
            "8500.00"
        )

        assert result_two[0] == "success"

    finally:
        db.close()