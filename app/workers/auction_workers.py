import time

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
    get_pending_outbox_events,
    mark_outbox_processed
)


def run_auction_worker():
    while True:

        process_outbox_events()

        # -------------------------
        # START AUCTIONS
        # -------------------------

        due_starts = get_due_auction_starts()

        if due_starts:
            print("Due auction starts:", due_starts)

        for auction_key in due_starts:
            auction_id = int(auction_key.split(":")[1])

            lock_key, lock_token = acquire_auction_lock(auction_id)

            if not lock_key:
                continue

            db = SessionLocal()

            try:
                auction = activate_auction(db, auction_id)

                if auction:
                    print(f"Auction {auction_id} is now ACTIVE")
                else:
                    print(f"Auction {auction_id} start was already processed")

                remove_auction_start(auction_id)

            except Exception as e:
                print(
                    f"Error activating auction {auction_id}: {e}"
                )

            finally:
                db.close()
                release_auction_lock(lock_key, lock_token)


        # -------------------------
        # END AUCTIONS
        # -------------------------

        due_ends = get_due_auction_ends()

        if due_ends:
            print("Due auction ends:", due_ends)

        for auction_key in due_ends:
            auction_id = int(auction_key.split(":")[1])

            lock_key, lock_token = acquire_auction_lock(auction_id)

            if not lock_key:
                continue

            db = SessionLocal()

            try:
                auction = end_auction(db, auction_id)

                if auction:
                    print(f"Auction {auction_id} is now ENDED")
                else:
                    print(f"Auction {auction_id} end was already processed")

                remove_auction_end(auction_id)

            except Exception as e:
                print(
                    f"Error ending auction {auction_id}: {e}"
                )

            finally:
                db.close()
                release_auction_lock(lock_key, lock_token)

        time.sleep(1)


def process_outbox_events():
    db = SessionLocal()

    try:
        events = get_pending_outbox_events(db)

        for event in events:

            if event.event_type == "AUCTION_CREATED":

                auction = get_auction_by_id(
                    db,
                    event.auction_id
                )

                if not auction:
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

                print(
                    f"Outbox event {event.id} processed "
                    f"For auction {auction.id}"
                )

    except Exception as e:
        db.rollback()
        print(f"Outbox processing error: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    run_auction_worker()