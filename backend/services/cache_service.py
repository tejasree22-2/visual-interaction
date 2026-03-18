import os
import json

_redis_client = None


def _get_redis_client():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    
    redis_url = os.environ.get("REDIS_URL")
    
    if not redis_url:
        print("REDIS_URL is not set in environment variables.")
        return None
    
    try:
        import redis
        _redis_client = redis.from_url(redis_url, decode_responses=True)
        _redis_client.ping()
        return _redis_client
    except Exception as e:
        print(f"Redis connection failed: {e}")
        _redis_client = None
        return None


def get_cached_result(key):
    client = _get_redis_client()
    if client is None:
        return None
    
    try:
        cached: str | None = client.get(key)  # type: ignore[assignment]
        if cached:
            return json.loads(cached)
    except Exception as e:
        print(f"Cache read error: {e}")
    return None


def set_cached_result(key, value):
    client = _get_redis_client()
    if client is None:
        return
    
    try:
        client.set(key, json.dumps(value))
    except Exception as e:
        print(f"Cache write error: {e}")


def clear_cache():
    client = _get_redis_client()
    if client:
        try:
            client.flushdb()
        except Exception as e:
            print(f"Cache clear error: {e}")
