from app.database import SessionLocal
from app.models.outbox import OutboxEvent

import app.services.auctions as auction_service
import app.workers.auction_workers as worker_module


def test_outbox_recovers_failed_redis_scheduling(
    user_factory,
    token_factory,
    auction_factory,
    monkeypatch
):
    # ---------------------------------
    # Simulate Redis being unavailable
    # during normal auction creation.
    # ---------------------------------

    def redis_failure(*args, **kwargs):
        raise ConnectionError(
            "Redis unavailable"
        )

    monkeypatch.setattr(
        auction_service,
        "schedule_auction_start",
        redis_failure
    )

    monkeypatch.setattr(
        auction_service,
        "schedule_auction_end",
        redis_failure
    )

    user_factory(
        "Seller",
        "seller@example.com"
    )

    seller_token = token_factory(
        "seller@example.com"
    )

    # Auction creation should still succeed because
    # PostgreSQL + outbox were committed successfully.
    auction = auction_factory(
        seller_token
    )

    # ---------------------------------
    # Verify event is still pending.
    # ---------------------------------

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
        assert event.processed_at is None

    finally:
        db.close()

    # ---------------------------------
    # Redis becomes available again.
    #
    # Instead of using real Redis, record what the
    # recovery worker attempts to schedule.
    # ---------------------------------

    scheduled_starts = []
    scheduled_ends = []

    def record_start(
        auction_id,
        start_time
    ):
        scheduled_starts.append(
            auction_id
        )

    def record_end(
        auction_id,
        end_time
    ):
        scheduled_ends.append(
            auction_id
        )

    monkeypatch.setattr(
        worker_module,
        "schedule_auction_start",
        record_start
    )

    monkeypatch.setattr(
        worker_module,
        "schedule_auction_end",
        record_end
    )

    # Manually trigger the same recovery function
    # the worker runs periodically.
    worker_module.process_outbox_events()

    # ---------------------------------
    # Verify recovery succeeded.
    # ---------------------------------

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

        assert event.processed_at is not None

        assert scheduled_starts == [
            auction["id"]
        ]

        assert scheduled_ends == [
            auction["id"]
        ]

    finally:
        db.close()