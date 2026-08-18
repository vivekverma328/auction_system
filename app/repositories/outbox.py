from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.outbox import OutboxEvent


def create_outbox_event(
    db: Session,
    event_type: str,
    auction_id: int
):
    event = OutboxEvent(
        event_type=event_type,
        auction_id=auction_id
    )

    db.add(event)

    return event


def get_pending_outbox_events(db: Session):
    return (
        db.query(OutboxEvent)
        .filter(OutboxEvent.processed_at.is_(None))
        .order_by(OutboxEvent.id)
        .all()
    )


def mark_outbox_processed(
    db: Session,
    event: OutboxEvent
):
    event.processed_at = datetime.now(timezone.utc)

    db.commit()