import os
from supabase import create_client, Client

_supabase_client: Client | None = None


def get_supabase_client() -> Client | None:
    global _supabase_client
    return _supabase_client


def init_supabase() -> Client | None:
    global _supabase_client
    
    connection_string = os.environ.get("SUPABASE_CONNECTION_STRING")
    
    if not connection_string:
        print("Supabase connection string not found. Please add SUPABASE_CONNECTION_STRING in the .env file.")
        return None
    
    _supabase_client = create_client(connection_string, connection_string)
    return _supabase_client


def store_simulation(angle: float, velocity: float, gravity: float) -> dict | None:
    client = get_supabase_client()
    
    if not client:
        client = init_supabase()
    
    if not client:
        return None
    
    data = {
        "angle": angle,
        "velocity": velocity,
        "gravity": gravity
    }
    
    response = client.table("simulations").insert(data).execute()
    return response.data
