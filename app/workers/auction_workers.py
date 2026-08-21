import time
import logging

from app.core.logging_config import configure_logging

from app.database import SessionLocal
from app.repositories.auctions import get_auction_by_id

from app.redis.scheduler import (
    get_due_auction_starts,
    get_due_auction_ends,
    remove_auction_start,
    remove_auction_end,
    schedule_auction_start,
    schedule_auction_end
)

from app.services.auctions import (
    activate_auction,
    end_auction
)

from app.redis.lock import (
    acquire_auction_lock,
    release_auction_lock
)

from app.repositories.outbox import (
    get_next_pending_outbox_event,
    mark_outbox_processed
)

configure_logging()

logger = logging.getLogger(__name__)

OUTBOX_POLL_INTERVAL = 30
WORKER_POLL_INTERVAL = 1
MAX_OUTBOX_EVENTS_PER_RUN = 100


def run_auction_worker():
    last_outbox_check = 0

    while True:
        current_time = time.monotonic()

        # ---------------------------------
        # OUTBOX RECOVERY
        # ---------------------------------

        if (
            current_time - last_outbox_check
            >= OUTBOX_POLL_INTERVAL
        ):
            process_outbox_events()

            last_outbox_check = current_time

        # ---------------------------------
        # START AUCTIONS
        # ---------------------------------

        due_starts = get_due_auction_starts()

        if due_starts:
            logger.info(
                "Due auction starts: %s",
                due_starts
            )

        for auction_key in due_starts:
            auction_id = int(
                auction_key.split(":")[1]
            )

            lock_key, lock_token = (
                acquire_auction_lock(
                    auction_id
                )
            )

            if not lock_key:
                continue

            db = SessionLocal()

            try:
                auction = activate_auction(
                    db,
                    auction_id
                )

                if auction:
                    logger.info(
                        "Auction %s is now ACTIVE",
                        auction_id
                    )
                else:
                    logger.info(
                        "Auction %s start was already processed",
                        auction_id
                    )

                remove_auction_start(
                    auction_id
                )

            except Exception:
                logger.exception(
                    "Failed to activate auction %s",
                    auction_id
                )

            finally:
                db.close()

                release_auction_lock(
                    lock_key,
                    lock_token
                )

        # ---------------------------------
        # END AUCTIONS
        # ---------------------------------

        due_ends = get_due_auction_ends()

        if due_ends:
            logger.info(
                "Due auction ends: %s",
                due_ends
            )

        for auction_key in due_ends:
            auction_id = int(
                auction_key.split(":")[1]
            )

            lock_key, lock_token = (
                acquire_auction_lock(
                    auction_id
                )
            )

            if not lock_key:
                continue

            db = SessionLocal()

            try:
                auction = end_auction(
                    db,
                    auction_id
                )

                if auction:
                    logger.info(
                        "Auction %s is now ENDED",
                        auction_id
                    )
                else:
                    logger.info(
                        "Auction %s start was already processed",
                        auction_id
                    )
                remove_auction_end(
                    auction_id
                )

            except Exception:
                logger.exception(
                    "Failed to end auction %s",
                    auction_id
                )

            finally:
                db.close()

                release_auction_lock(
                    lock_key,
                    lock_token
                )

        time.sleep(
            WORKER_POLL_INTERVAL
        )


def process_outbox_events():
    for _ in range(
        MAX_OUTBOX_EVENTS_PER_RUN
    ):
        db = SessionLocal()

        try:
            event = (
                get_next_pending_outbox_event(
                    db
                )
            )

            if event is None:
                return

            if event.event_type != "AUCTION_CREATED":
                logger.warning(
                    "Unknown outbox event type: %s",
                    event.event_type
                )

                mark_outbox_processed(
                    db,
                    event
                )

                continue

            auction = get_auction_by_id(
                db,
                event.auction_id
            )

            if auction is None:
                logger.warning(
                    "Auction %s for outbox event %s does not exist",
                    event.auction_id,
                    event.id
                )

                mark_outbox_processed(
                    db,
                    event
                )

                continue

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
                event
            )

            logger.info(
                "Recovered outbox event %s for auction %s",
                event.id,
                auction.id
            )

        except Exception:
            db.rollback()

            logger.exception(
                "Outbox recovery failed"
            )

            # Redis may still be unavailable.
            # Don't retry the same event 100 times
            # in the same worker cycle.
            return

        finally:
            db.close()


if __name__ == "__main__":
    run_auction_worker()