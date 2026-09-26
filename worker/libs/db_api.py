from supabase import Client
from postgrest.exceptions import APIError

def get_all_rows(client: Client, table_name: str, columns: str ='*'):
    """
    Fetches all rows from a Supabase table, automatically paginating 
    in chunks of 1,000 rows until the entire table is retrieved.
    """
    all_data = []
    chunk_size = 1000
    start_index = 0
    
    print(f"Starting bulk fetch from table: '{table_name}'...")
    
    while True:
        end_index = start_index + chunk_size - 1
        
        try:
            # Request a specific slice of rows (e.g., 0-999, 1000-1999)
            response = (
                client.table(table_name)
                .select(columns)
                .range(start_index, end_index)
                .execute()
            )
            
            chunk_data = response.data
            
            # If no data is returned, we've hit the end of the table
            if not chunk_data:
                break
                
            all_data.extend(chunk_data)
            print(f"Fetched rows {start_index} to {start_index + len(chunk_data) - 1}")
            
            # Move the window forward for the next loop
            start_index += chunk_size
            
            # If the chunk returned is smaller than 1000, it was the final page
            if len(chunk_data) < chunk_size:
                break
                
        except APIError as e:
            print(f"Supabase API Error during pagination: {e.message} (Code: {e.code})")
            raise e
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise e
            
    print(f"Successfully fetched all {len(all_data)} rows from '{table_name}'.")
    return all_data

def get_map_ids(client: Client):
    data = []
    try:
        data = get_all_rows(client, "Map", "tmx_id,uid")
    except APIError as e:
        print(f"{e.code}: {e.message}")
    return data

def get_all_identities(client: Client):
    data = []
    try:
        data = get_all_rows(client, "PlayerIdentity", "provider,external_id,username")
    except APIError as e:
        print(f"{e.code}: {e.message}")
    return data

def upsert_records(client: Client, data: list[dict]):
    try:
        client.table("Record").upsert(data, on_conflict="map_uid,player_identity_id,leaderboard").execute()
    except APIError as e:
        print(f"{e.code}: {e.message}")

def upsert_players(client: Client, data: list[dict]):
    try:
        client.table("PlayerIdentity").upsert(data, on_conflict="provider,external_id").execute()
    except APIError as e:
        print(f"{e.code}: {e.message}")

def sync_connected_components(
    components: list[list[tuple[str, str]]], id_name_map: dict, client: Client
):
    # 1. Filter valid clusters (N >= 2)
    valid_clusters = [c for c in components if len(c) >= 2]
    if not valid_clusters:
        return

    # 2. Collect ALL identity keys for a single RPC call
    all_identities = [
        {"provider": node[0], "external_id": node[1]}
        for cluster in valid_clusters
        for node in cluster
    ]

    # 3. SINGLE ROUNDTRIP: Fetch all matched identities across all clusters
    existing_response = client.rpc(
        "get_matched_identities", {"identities": all_identities}
    ).execute()

    # Map (provider, external_id) -> profile_id in memory
    identity_to_profile = {
        (row["provider"], row["external_id"]): row["profile_id"]
        for row in existing_response.data
    }

    # 4. Resolve profiles per cluster in memory
    clusters_needing_profiles = []
    cluster_to_target_profile = {}
    deprecated_profile_ids = set()

    for idx, cluster in enumerate(valid_clusters):
        matched_profiles = list(
            {
                identity_to_profile[(node[0], node[1])]
                for node in cluster
                if (node[0], node[1]) in identity_to_profile
            }
        )

        if not matched_profiles:
            # Mark for batch insertion (use first username as display name)
            item = 0
            while item < len(cluster) and id_name_map[cluster[item][1]] == None:
                item += 1
            clusters_needing_profiles.append((idx, id_name_map[cluster[item][1]]))
            print(item, id_name_map[cluster[item][1]])
        elif len(matched_profiles) == 1:
            cluster_to_target_profile[idx] = matched_profiles[0]
        else:
            # Merge case: choose survivor, mark others as deprecated
            survivor_id = matched_profiles[0]
            cluster_to_target_profile[idx] = survivor_id
            deprecated_profile_ids.update(matched_profiles[1:])

    # 5. BATCH INSERT: Create all required new profiles in 1 request
    if clusters_needing_profiles:
        new_profile_payload = [
            {"display_name": name, "role": "GUEST"}
            for _, name in clusters_needing_profiles
        ]
        inserted_profiles = (
            client.table("Profile").insert(new_profile_payload).execute()
        )

        for (idx, _), new_profile in zip(
            clusters_needing_profiles, inserted_profiles.data
        ):
            cluster_to_target_profile[idx] = new_profile["id"]

    # 6. BATCH MERGE: Handle deprecated profiles if any exist
    if deprecated_profile_ids:
        # Transfer identity links to survivors then clean up
        for old_id in deprecated_profile_ids:
            target_id = next(
                pid
                for pid in cluster_to_target_profile.values()
                if pid not in deprecated_profile_ids
            )
            client.table("MatchedIdentity").update(
                {"profile_id": target_id}
            ).eq("profile_id", old_id).execute()
            client.table("Profile").update({"merged_into_id": target_id}).eq("id", old_id).execute()

    # 7. BATCH UPSERT: Build and upload ALL MatchedIdentity records at once
    all_matched_records = []
    for idx, cluster in enumerate(valid_clusters):
        target_profile_id = cluster_to_target_profile[idx]
        for node in cluster:
            all_matched_records.append(
                {
                    "provider": node[0],
                    "external_id": node[1],
                    "profile_id": target_profile_id,
                }
            )

    client.table("MatchedIdentity").upsert(
        all_matched_records, on_conflict="provider, external_id, profile_id"
    ).execute()

def get_all_profiles(client: Client):
    data = []
    try:
        data = get_all_rows(client, "Profile", "MatchedIdentity(*)")
    except APIError as e:
        print(f"{e.code}: {e.message}")
    return data