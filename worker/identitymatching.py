from requests import Session
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from requests import Session
from libs import utils, db_api
from collections import deque
import uuid
from test import get_profile_relations, update_relation_graph

load_dotenv()

# Replace with your actual project keys from Supabase dashboard
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY") # Use service role if bypasses RLS is needed for backend

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
session = Session()

def update_profiles(client: Client, session: Session):
    profiles = db_api.get_all_profiles(client)
    user_ids = db_api.get_all_identities(client)
    id_name_map = {int(id["external_id"]) if id["provider"]=="TMX" else id["external_id"]: id["username"] for id in user_ids}
    relation_graph = utils.construct_profile_graph(profiles, user_ids)
    relations = get_profile_relations(session, relation_graph, user_ids)
    update_relation_graph(client, relation_graph, relations)
    update_identities = []
    updated_profiles = []
    while relation_graph:
        queue = deque()
        nodes = set()
        queue.append(list(relation_graph.keys())[0])
        while queue:
            node = queue.popleft()
            if node not in relation_graph.keys():
                continue
            for child in relation_graph[node]:
                queue.append(child)
            nodes.add(("TMX" if type(node) == int else "DEDIMANIA", node))
            update_identities.append({"provider": "TMX" if type(node) == int else "DEDIMANIA", "external_id": node})
            relation_graph.pop(node)
        updated_profiles.append(list(nodes))

    supabase.table("PlayerIdentity").upsert(update_identities, on_conflict="provider, external_id").execute()

    print("Syncing relations")
    db_api.sync_connected_components(updated_profiles, id_name_map, client)