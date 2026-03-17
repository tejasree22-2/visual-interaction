import os
import json
import redis


_redis_client = None


def _get_redis_client():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    
    redis_url = os.environ.get("REDIS_URL")
    
    if not redis_url:
        print("REDIS_URL is not set in environment variables.")
        print("Please add REDIS_URL to your .env file (e.g., redis://localhost:6379/0)")
        return None
    
    _redis_client = redis.from_url(redis_url)
    return _redis_client


def get_cached_result(key):
    client = _get_redis_client()
    if client is None:
        return None
    
    cached = client.get(key)
    if cached:
        return json.loads(cached)
    return None


def set_cached_result(key, value):
    client = _get_redis_client()
    if client is None:
        return
    
    client.set(key, json.dumps(value))


def clear_cache():
    client = _get_redis_client()
    if client:
        client.flushdb()
