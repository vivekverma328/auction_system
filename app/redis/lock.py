from uuid import uuid4

from app.redis.client import redis_client

def acquire_auction_lock(auction_id: int, expiry: int = 10):
    lock_key = f"auction:{auction_id}:lock"
    lock_token = str(uuid4())

    acquired = redis_client.set(
        lock_key,
        lock_token,
        nx=True,
        ex=expiry
    )

    if acquired:
        return lock_key, lock_token

    return None, None

def release_auction_lock(lock_key: str, lock_token: str):
    script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """

    redis_client.eval(
        script,
        1,
        lock_key,
        lock_token
    )