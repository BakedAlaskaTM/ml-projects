from supabase import create_client, Client
from dotenv import load_dotenv
import os
from libs import utils, db_api

load_dotenv()

def parse_external_id(id_str: str, provider: str):
    if provider == "TMX":
        return int(id_str)
    return id_str

# Replace with your actual project keys from Supabase dashboard
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY") # Use service role if bypasses RLS is needed for backend

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
profiles = db_api.get_all_profiles(supabase)
user_ids = db_api.get_all_identities(supabase)

id_name_map = {parse_external_id(id["external_id"], id["provider"]): id["username"] for id in user_ids}

graph = {parse_external_id(id["external_id"], id["provider"]): [] for id in user_ids}

for profile in profiles:
    linked_identities = profile["MatchedIdentity"]
    for i in range(len(linked_identities)):
        target_id = linked_identities[i]
        graph[parse_external_id(target_id["external_id"], target_id["provider"])] = [parse_external_id(identity["external_id"], identity["provider"]) for identity in linked_identities if identity["external_id"] != target_id["external_id"]]



print(graph)