import re
import json
import os
import time as T
from postgrest.exceptions import APIError
from supabase import create_client, Client
from dotenv import load_dotenv
import api




if __name__ == "__main__":
    # Load variables from .env into system environment
    load_dotenv()

    # Replace with your actual project keys from Supabase dashboard
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY") # Use service role if bypasses RLS is needed for backend

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    print(api.get_all_rows(supabase, "ProjectMap", "*, Map(*), Project(*)"))