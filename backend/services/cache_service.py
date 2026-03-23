import os
import json
import logging
from datetime import datetime

logger = logging.getLogger('visual-interaction-backend.cache')

_redis_client = None
_redis_initialized = False

CACHE_TTL = 3600


def _get_redis_client():
    global _redis_client, _redis_initialized
    
    if _redis_client is not None:
        return _redis_client
    
    if _redis_initialized:
        return None
    
    _redis_initialized = True
    redis_url = os.environ.get("REDIS_URL")
    
    if not redis_url:
        logger.warning("Redis: REDIS_URL not set - caching disabled")
        return None
    
    try:
        import redis
        logger.info("Redis: Connecting...")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
        _redis_client.ping()
        logger.info("Redis: Connected successfully")
        return _redis_client
    except Exception as e:
        logger.error(f"Redis: Connection failed - {e}")
        _redis_client = None
        return None


def get_cached_result(key):
    client = _get_redis_client()
    if client is None:
        return None
    
    try:
        cached = client.get(key)
        if cached and isinstance(cached, str):
            logger.info(f"Cache: HIT - {key}")
            return json.loads(cached)
    except Exception as e:
        logger.error(f"Cache: Read error - {e}")
    return None


def set_cached_result(key, value):
    client = _get_redis_client()
    if client is None:
        return
    
    try:
        client.setex(key, CACHE_TTL, json.dumps(value))
        logger.info(f"Cache: Saved - {key}")
    except Exception as e:
        logger.error(f"Cache: Write error - {e}")


def clear_cache():
    client = _get_redis_client()
    if client:
        try:
            client.flushdb()
            logger.info("Cache: Cleared")
        except Exception as e:
            logger.error(f"Cache: Clear error - {e}")


CHANGES_TTL = 7200
_changes_history = {}


def track_user_change(session_id: str, changes: dict) -> dict:
    global _changes_history
    
    change_entry = {
        'timestamp': datetime.now().isoformat(),
        'changes': changes,
        'field': changes.get('field', 'unknown'),
        'old_value': changes.get('old_value'),
        'new_value': changes.get('new_value')
    }
    
    if session_id not in _changes_history:
        _changes_history[session_id] = []
        logger.info(f"New session tracking: {session_id}")
    
    _changes_history[session_id].append(change_entry)
    
    if len(_changes_history[session_id]) > 100:
        _changes_history[session_id] = _changes_history[session_id][-100:]
    
    logger.info(f"Track change: {change_entry['field']} = {change_entry['old_value']} → {change_entry['new_value']}")
    
    client = _get_redis_client()
    if client:
        try:
            changes_key = f"user_changes:{session_id}"
            client.lpush(changes_key, json.dumps(change_entry))
            client.ltrim(changes_key, 0, 99)
            client.expire(changes_key, CHANGES_TTL)
        except Exception as e:
            logger.error(f"Cache: Failed to save user changes - {e}")
    
    return change_entry


def get_user_changes(session_id: str, limit: int = 50) -> list:
    client = _get_redis_client()
    
    if client:
        try:
            changes_key = f"user_changes:{session_id}"
            cached_changes = client.lrange(changes_key, 0, limit - 1)
            if cached_changes:
                return [json.loads(c) for c in cached_changes]
        except Exception as e:
            logger.error(f"Cache: Failed to retrieve user changes - {e}")
    
    return _changes_history.get(session_id, [])[-limit:]


def clear_user_changes(session_id: str):
    global _changes_history
    
    if session_id in _changes_history:
        del _changes_history[session_id]
        logger.info(f"Cleared history for session: {session_id}")
    
    client = _get_redis_client()
    if client:
        try:
            changes_key = f"user_changes:{session_id}"
            client.delete(changes_key)
        except Exception as e:
            logger.error(f"Cache: Failed to clear user changes - {e}")
