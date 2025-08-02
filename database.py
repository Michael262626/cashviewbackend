import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file if it exists
load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise Exception("Supabase credentials are missing")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase_client() -> Client:
    """Return the Supabase client instance"""
    return supabase
