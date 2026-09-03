from postgrest.exceptions import APIError
from supabase import create_client, Client

def get_all_rows(client: Client, table_name, columns='*'):
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

def get_project_by_slug(client: Client, slug: str):
    try:
        response = (client.table("Project").select("*").eq("slug", slug).limit(1).execute())
        return response.data
    except APIError as e:
        print(f"API Error: {e.message} (Code: {e.code})")
    return None

def get_tracks_by_project_slug(client: Client, slug: str):
    """
    Fetches all rows from a Supabase table, automatically paginating 
    in chunks of 1,000 rows until the entire table is retrieved.
    """
    all_data = []
    chunk_size = 1000
    start_index = 0
    
    print(f"Starting bulk fetch from table: 'Map'...")
    
    while True:
        end_index = start_index + chunk_size - 1
        
        try:
            # Request a specific slice of rows (e.g., 0-999, 1000-1999)
            response = (
                client.table("Map")
                .select("*")
                .eq("project_slug", slug)
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
            
    print(f"Successfully fetched all {len(all_data)} rows from 'Map'.")
    return all_data


def upsert_projects(client: Client, data: list[dict]):
    print("Upserting projects")
    try:
        client.table("Project").upsert(data, on_conflict="slug").execute()
        print("Complete")
    except APIError as e:
        print(f"Error code: {e.code}")
        print(f"Error message: {e.message}")

def upsert_maps(client: Client, data: list[dict]):
    print("Upserting maps")
    try:
        client.table("Map").upsert(data, on_conflict="uid,project_slug").execute()
        print("Complete")
    except APIError as e:
        print(f"Error code: {e.code}")
        print(f"Error message: {e.message}")