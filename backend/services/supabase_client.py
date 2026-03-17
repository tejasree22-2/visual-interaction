import os
import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_connection():
    connection_string = os.environ.get("SUPABASE_CONNECTION_STRING")
    if not connection_string:
        print("SUPABASE_CONNECTION_STRING not found in .env")
        return None
    return psycopg2.connect(connection_string)


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
            return {"success": True}
    except Exception as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()
