from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime, timezone

from app.models.base import Base


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(Integer, primary_key=True, index=True)

    event_type = Column(String, nullable=False)

    auction_id = Column(
        Integer,
        ForeignKey("auctions.id"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    processed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )