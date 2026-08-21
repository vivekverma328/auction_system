import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL environment variable is not set"
    )


# This must happen before importing app.database/app.main.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Redis won't actually be used during these API tests,
# but client.py expects these variables to exist.
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")


from app.database import SessionLocal, engine
from app.main import app
from app.models.auctions import Auction
from app.models.base import Base
from app.models.bids import Bid
from app.models.outbox import OutboxEvent
from app.models.users import User

import app.services.auctions as auction_service


@pytest.fixture(autouse=True)
def clean_database(monkeypatch):
    """
    Create a fresh schema for every test.

    Redis scheduling is mocked because these tests focus on
    HTTP APIs and PostgreSQL business logic.
    """

    monkeypatch.setattr(
        auction_service,
        "schedule_auction_start",
        lambda *args, **kwargs: None
    )

    monkeypatch.setattr(
        auction_service,
        "schedule_auction_end",
        lambda *args, **kwargs: None
    )

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def user_factory(client):
    def create_user(
        name: str,
        email: str,
        password: str = "Password123"
    ):
        response = client.post(
            "/users/",
            json={
                "name": name,
                "email": email,
                "password": password
            }
        )

        assert response.status_code == 200

        return response.json()

    return create_user


@pytest.fixture
def token_factory(client):
    def get_token(
        email: str,
        password: str = "Password123"
    ):
        response = client.post(
            "/auth/login",
            data={
                "username": email,
                "password": password
            }
        )

        assert response.status_code == 200

        return response.json()["access_token"]

    return get_token


@pytest.fixture
def add_balance(client):
    def update_balance(
        token: str,
        amount: Decimal
    ):
        response = client.patch(
            "/users/me/balance",
            headers={
                "Authorization": f"Bearer {token}"
            },
            json={
                "account_balance": str(amount)
            }
        )

        assert response.status_code == 200

        return response.json()

    return update_balance


@pytest.fixture
def auction_factory(client):
    def create_auction(
        seller_token: str,
        starting_price: Decimal = Decimal("1000.00")
    ):
        start_time = (
            datetime.now(timezone.utc)
            + timedelta(minutes=1)
        )

        end_time = (
            start_time
            + timedelta(minutes=6)
        )

        response = client.post(
            "/auctions/",
            headers={
                "Authorization": f"Bearer {seller_token}"
            },
            json={
                "title": "Gold Ring",
                "description": "22 carat gold ring",
                "starting_price": str(starting_price),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
        )

        assert response.status_code == 200

        return response.json()

    return create_auction


@pytest.fixture
def activate_auction():
    def make_active(auction_id: int):
        db = SessionLocal()

        try:
            auction = (
                db.query(Auction)
                .filter(Auction.id == auction_id)
                .first()
            )

            assert auction is not None

            auction.status = "ACTIVE"

            db.commit()

        finally:
            db.close()

    return make_active