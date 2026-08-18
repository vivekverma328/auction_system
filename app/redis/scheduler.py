START_SCHEDULE = "auction:start_schedule"
END_SCHEDULE = "auction:end_schedule"

from app.redis.client import redis_client

from datetime import datetime
import time

def schedule_auction_start(auction_id: int, start_time: datetime):
    timestamp = start_time.timestamp()

    redis_client.zadd(
        START_SCHEDULE,
        {f"auction:{auction_id}": timestamp}
    )

def schedule_auction_end(auction_id: int, end_time: datetime):
    timestamp = end_time.timestamp()

    redis_client.zadd(
        END_SCHEDULE,
        {f"auction:{auction_id}":timestamp}
    )

def get_due_auction_starts():
    current_timestamp = time.time()

    due_auctions = redis_client.zrangebyscore(
        START_SCHEDULE,
        min='-inf',
        max=current_timestamp
    )

    return due_auctions

def get_due_auction_ends():
    current_timestamp = time.time()

    due_auctions = redis_client.zrangebyscore(
        END_SCHEDULE,
        min='-inf',
        max=current_timestamp
    )

    return due_auctions

def remove_auction_start(auction_id: int):
    redis_client.zrem(
        START_SCHEDULE,
        f"auction:{auction_id}"
    )

def remove_auction_end(auction_id: int):
    redis_client.zrem(
        END_SCHEDULE,
        f"auction:{auction_id}"
    )