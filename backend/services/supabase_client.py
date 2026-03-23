import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger('visual-interaction-backend.database')

_db_initialized = False
_db_available = None


def get_db_connection():
    global _db_initialized, _db_available
    
    connection_string = os.environ.get("SUPABASE_CONNECTION_STRING")
    if not connection_string:
        if not _db_initialized:
            logger.warning("Database: SUPABASE_CONNECTION_STRING not set")
            _db_initialized = True
        return None
    
    if _db_available is False:
        return None
    
    try:
        conn = psycopg2.connect(connection_string)
        if not _db_initialized:
            logger.info("Database: Connected to Supabase PostgreSQL")
            _db_initialized = True
        _db_available = True
        return conn
    except Exception as e:
        logger.error(f"Database: Connection failed - {e}")
        _db_initialized = True
        _db_available = False
        return None


def store_simulation(angle: float, velocity: float, gravity: float) -> dict | None:
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO simulations (angle, velocity, gravity) VALUES (%s, %s, %s) RETURNING id",
                (angle, velocity, gravity)
            )
            conn.commit()
            logger.info(f"Database: Saved simulation (angle={angle}, velocity={velocity}, gravity={gravity})")
            return {"success": True}
    except Exception as e:
        logger.error(f"Database: Error saving simulation - {e}")
        return None
    finally:
        if conn:
            conn.close()
