import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def create_supabase_client():

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_PUBLISHABLE_KEY")

    if not supabase_url:
        raise ValueError("SUPABASE_URL is missing!")

    if not supabase_key:
        raise ValueError("SUPABASE_PUBLISHABLE_KEY is missing!")

    # Connect to Supabase
    supabase = create_client(
        supabase_url,
        supabase_key
    )

    return supabase