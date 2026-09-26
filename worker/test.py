from requests import Session, adapters
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from requests import Session
from libs import utils, records_api, db_api

def get_profile_relations(session: Session, relation_graph: dict, user_ids: list[dict]) -> list[dict]:
    tmx_ids = [row["external_id"] for row in user_ids if (row["provider"]=="TMX" and not relation_graph[utils.parse_external_id(row["external_id"], row["provider"])])]

    print(tmx_ids)

    sample_ids = records_api.get_sample_replays(session, tmx_ids, LIST_COUNT, SAMPLE_SIZE)
    print("Getting logins")
    logins = records_api.find_logins(session, sample_ids)
    return logins

def update_relation_graph(client: Client, relation_graph: dict, relations: list[tuple[str, str]]):
    for r in relations:
        tmx = int(r[0])
        login = r[1]
        relation_graph[tmx].add(login)
        if login not in relation_graph.keys():
            relation_graph[login] = [tmx]
        else:
            relation_graph[login].add(tmx)

    flagged_tmx = set()
    for node, edges in relation_graph.items():
        if type(node) == int and any((isinstance(item, int) or any(isinstance(child_item, int) for child_item in relation_graph[item] if child_item != node)) for item in edges):
            flagged_tmx.add(node)

    player_identity_update = [{"provider": "TMX", "external_id": id, "flagged": True} for id in flagged_tmx]
    db_api.upsert_players(client, player_identity_update)
    return True


if __name__ == "__main__":
    LIST_COUNT = 50
    SAMPLE_SIZE = 15

    load_dotenv()

    # Replace with your actual project keys from Supabase dashboard
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY") # Use service role if bypasses RLS is needed for backend

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    session = Session()
    adapter = adapters.HTTPAdapter(pool_connections=8, pool_maxsize=8)
    session.mount('https://', adapter)

    profiles = db_api.get_all_profiles(supabase)
    user_ids = db_api.get_all_identities(supabase)

    relation_graph = utils.construct_profile_graph(profiles, user_ids)

    relations = get_profile_relations(session, relation_graph, user_ids)

    update_relation_graph(supabase, relation_graph, relations)