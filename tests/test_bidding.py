from decimal import Decimal

from app.database import SessionLocal
from app.models.auctions import Auction
from app.services.auctions import end_auction


def get_balance(client, user_id: int):
    response = client.get(
        f"/users/{user_id}"
    )

    assert response.status_code == 200

    return Decimal(
        response.json()["account_balance"]
    )


def prepare_active_auction(
    user_factory,
    token_factory,
    auction_factory,
    activate_auction
):
    seller = user_factory(
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

    return seller, seller_token, auction


def test_successful_bid_reserves_balance(
    client,
    user_factory,
    token_factory,
    add_balance,
    auction_factory,
    activate_auction
):
    seller, _, auction = prepare_active_auction(
        user_factory,
        token_factory,
        auction_factory,
        activate_auction
    )

    bidder = user_factory(
        "Bidder",
        "bidder@example.com"
    )

    bidder_token = token_factory(
        "bidder@example.com"
    )

    add_balance(
        bidder_token,
        Decimal("10000.00")
    )

    response = client.post(
        "/bids/",
        headers={
            "Authorization": f"Bearer {bidder_token}"
        },
        json={
            "auction_id": auction["id"],
            "amount": "1200.00"
        }
    )

    assert response.status_code == 200
    assert Decimal(
        response.json()["amount"]
    ) == Decimal("1200.00")

    balance = get_balance(
        client,
        bidder["id"]
    )

    assert balance == Decimal("8800.00")


def test_seller_cannot_bid(
    client,
    user_factory,
    token_factory,
    add_balance,
    auction_factory,
    activate_auction
):
    seller, seller_token, auction = (
        prepare_active_auction(
            user_factory,
            token_factory,
            auction_factory,
            activate_auction
        )
    )

    add_balance(
        seller_token,
        Decimal("10000.00")
    )

    response = client.post(
        "/bids/",
        headers={
            "Authorization": f"Bearer {seller_token}"
        },
        json={
            "auction_id": auction["id"],
            "amount": "1200.00"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Seller cannot bid on their own auction"
    )


def test_bid_must_exceed_highest_bid(
    client,
    user_factory,
    token_factory,
    add_balance,
    auction_factory,
    activate_auction
):
    _, _, auction = prepare_active_auction(
        user_factory,
        token_factory,
        auction_factory,
        activate_auction
    )

    bidder = user_factory(
        "Bidder",
        "bidder@example.com"
    )

    bidder_token = token_factory(
        "bidder@example.com"
    )

    add_balance(
        bidder_token,
        Decimal("10000.00")
    )

    response = client.post(
        "/bids/",
        headers={
            "Authorization": f"Bearer {bidder_token}"
        },
        json={
            "auction_id": auction["id"],
            "amount": "900.00"
        }
    )

    assert response.status_code == 400


def test_insufficient_balance_rejected(
    client,
    user_factory,
    token_factory,
    add_balance,
    auction_factory,
    activate_auction
):
    _, _, auction = prepare_active_auction(
        user_factory,
        token_factory,
        auction_factory,
        activate_auction
    )

    user_factory(
        "Bidder",
        "bidder@example.com"
    )

    bidder_token = token_factory(
        "bidder@example.com"
    )

    add_balance(
        bidder_token,
        Decimal("1000.00")
    )

    response = client.post(
        "/bids/",
        headers={
            "Authorization": f"Bearer {bidder_token}"
        },
        json={
            "auction_id": auction["id"],
            "amount": "1500.00"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Insufficient account balance"
    )


def test_previous_bidder_is_refunded(
    client,
    user_factory,
    token_factory,
    add_balance,
    auction_factory,
    activate_auction
):
    _, _, auction = prepare_active_auction(
        user_factory,
        token_factory,
        auction_factory,
        activate_auction
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

    first_bid = client.post(
        "/bids/",
        headers={
            "Authorization": f"Bearer {token_one}"
        },
        json={
            "auction_id": auction["id"],
            "amount": "1200.00"
        }
    )

    assert first_bid.status_code == 200

    second_bid = client.post(
        "/bids/",
        headers={
            "Authorization": f"Bearer {token_two}"
        },
        json={
            "auction_id": auction["id"],
            "amount": "1500.00"
        }
    )

    assert second_bid.status_code == 200

    assert get_balance(
        client,
        bidder_one["id"]
    ) == Decimal("10000.00")

    assert get_balance(
        client,
        bidder_two["id"]
    ) == Decimal("8500.00")


def test_same_bidder_can_raise_bid(
    client,
    user_factory,
    token_factory,
    add_balance,
    auction_factory,
    activate_auction
):
    _, _, auction = prepare_active_auction(
        user_factory,
        token_factory,
        auction_factory,
        activate_auction
    )

    bidder = user_factory(
        "Bidder",
        "bidder@example.com"
    )

    bidder_token = token_factory(
        "bidder@example.com"
    )

    add_balance(
        bidder_token,
        Decimal("10000.00")
    )

    first_response = client.post(
        "/bids/",
        headers={
            "Authorization": f"Bearer {bidder_token}"
        },
        json={
            "auction_id": auction["id"],
            "amount": "1200.00"
        }
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/bids/",
        headers={
            "Authorization": f"Bearer {bidder_token}"
        },
        json={
            "auction_id": auction["id"],
            "amount": "1800.00"
        }
    )

    assert second_response.status_code == 200

    assert get_balance(
        client,
        bidder["id"]
    ) == Decimal("8200.00")


def test_bid_on_ended_auction_fails(
    client,
    user_factory,
    token_factory,
    add_balance,
    auction_factory,
    activate_auction
):
    _, _, auction = prepare_active_auction(
        user_factory,
        token_factory,
        auction_factory,
        activate_auction
    )

    bidder = user_factory(
        "Bidder",
        "bidder@example.com"
    )

    bidder_token = token_factory(
        "bidder@example.com"
    )

    add_balance(
        bidder_token,
        Decimal("10000.00")
    )

    db = SessionLocal()

    try:
        auction_row = (
            db.query(Auction)
            .filter(
                Auction.id == auction["id"]
            )
            .first()
        )

        auction_row.status = "ENDED"
        db.commit()

    finally:
        db.close()

    response = client.post(
        "/bids/",
        headers={
            "Authorization": f"Bearer {bidder_token}"
        },
        json={
            "auction_id": auction["id"],
            "amount": "1200.00"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Bids can only be placed on ACTIVE auctions"
    )


def test_auction_settlement_pays_seller(
    client,
    user_factory,
    token_factory,
    add_balance,
    auction_factory,
    activate_auction
):
    seller, seller_token, auction = (
        prepare_active_auction(
            user_factory,
            token_factory,
            auction_factory,
            activate_auction
        )
    )

    add_balance(
        seller_token,
        Decimal("5000.00")
    )

    bidder = user_factory(
        "Bidder",
        "bidder@example.com"
    )

    bidder_token = token_factory(
        "bidder@example.com"
    )

    add_balance(
        bidder_token,
        Decimal("10000.00")
    )

    response = client.post(
        "/bids/",
        headers={
            "Authorization": f"Bearer {bidder_token}"
        },
        json={
            "auction_id": auction["id"],
            "amount": "2000.00"
        }
    )

    assert response.status_code == 200

    db = SessionLocal()

    try:
        ended_auction = end_auction(
            db,
            auction["id"]
        )

        assert ended_auction.status == "ENDED"

    finally:
        db.close()

    assert get_balance(
        client,
        seller["id"]
    ) == Decimal("7000.00")

    assert get_balance(
        client,
        bidder["id"]
    ) == Decimal("8000.00")


def test_bid_history_pagination(
    client,
    user_factory,
    token_factory,
    add_balance,
    auction_factory,
    activate_auction
):
    _, _, auction = prepare_active_auction(
        user_factory,
        token_factory,
        auction_factory,
        activate_auction
    )

    user_factory(
        "Bidder",
        "bidder@example.com"
    )

    bidder_token = token_factory(
        "bidder@example.com"
    )

    add_balance(
        bidder_token,
        Decimal("10000.00")
    )

    for amount in (
        "1200.00",
        "1500.00",
        "1800.00"
    ):
        response = client.post(
            "/bids/",
            headers={
                "Authorization": f"Bearer {bidder_token}"
            },
            json={
                "auction_id": auction["id"],
                "amount": amount
            }
        )

        assert response.status_code == 200

    response = client.get(
        f"/auctions/{auction['id']}/bids"
        "?limit=2&offset=1"
    )

    assert response.status_code == 200
    assert len(response.json()) == 2