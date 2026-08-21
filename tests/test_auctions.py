from app.database import SessionLocal
from app.models.outbox import OutboxEvent


def test_create_auction(
    client,
    user_factory,
    token_factory,
    auction_factory
):
    seller = user_factory(
        "Seller",
        "seller@example.com"
    )

    token = token_factory(
        "seller@example.com"
    )

    auction = auction_factory(token)

    assert auction["seller_id"] == seller["id"]
    assert auction["status"] == "SCHEDULED"
    assert auction["title"] == "Gold Ring"


def test_auction_creation_processes_outbox(
    client,
    user_factory,
    token_factory,
    auction_factory
):
    user_factory(
        "Seller",
        "seller@example.com"
    )

    token = token_factory(
        "seller@example.com"
    )

    auction = auction_factory(token)

    db = SessionLocal()

    try:
        event = (
            db.query(OutboxEvent)
            .filter(
                OutboxEvent.auction_id
                == auction["id"]
            )
            .first()
        )

        assert event is not None
        assert event.event_type == "AUCTION_CREATED"

        # Our mocked Redis calls succeeded,
        # so normal fast-path delivery should mark
        # the outbox event processed.
        assert event.processed_at is not None

    finally:
        db.close()


def test_get_auction(
    client,
    user_factory,
    token_factory,
    auction_factory
):
    user_factory(
        "Seller",
        "seller@example.com"
    )

    token = token_factory(
        "seller@example.com"
    )

    auction = auction_factory(token)

    response = client.get(
        f"/auctions/{auction['id']}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == auction["id"]


def test_auction_pagination(
    client,
    user_factory,
    token_factory,
    auction_factory
):
    user_factory(
        "Seller",
        "seller@example.com"
    )

    token = token_factory(
        "seller@example.com"
    )

    auction_factory(token)
    auction_factory(token)
    auction_factory(token)

    response = client.get(
        "/auctions/?limit=2&offset=0"
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_invalid_pagination_rejected(client):
    response = client.get(
        "/auctions/?limit=0"
    )

    assert response.status_code == 422