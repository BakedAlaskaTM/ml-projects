import json
import secrets
import urllib.parse as p
from enum import Enum, auto

class By(Enum):
    UID = auto()
    PROJECT_SLUG = auto()

def format_time(ms):
    seconds = ms / 1000
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    # Build string dynamically based on the highest non-zero unit
    if hours > 0:
        return f"{int(hours)}:{int(minutes):02d}:{seconds:05.2f}"
    elif minutes > 0:
        return f"{int(minutes)}:{seconds:05.2f}"
    else:
        return f"{seconds:.2f}"

def write_json(filename: str, data):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=True)

def generate_slug(length_bytes: int = 6) -> str:
    return secrets.token_urlsafe(length_bytes)

def flatten_project_data(project_name: str, project_slug: str):
    return [{"name": project_name, "slug": project_slug, "is_active": True}]

def flatten_selected_tracks(tracks: dict):
    flattened = []
    for track_info in tracks.values():
        flattened.append({
            "uid": track_info["UId"],
            "tmx_id": track_info["TrackId"],
            "name": track_info["TrackName"],
            "tmx_author_id": [author["UserId"] for author in track_info["Authors"]],
            "author_time": track_info["AuthorTime"]
        })
    return flattened

def construct_selected_tracks(flattened: list[dict]):
    selected_tracks = {}
    for track_info in flattened:
        selected_tracks[track_info["uid"]] = {
            "UId": track_info["uid"],
            "TrackId": track_info["tmx_id"],
            "TrackName": track_info["name"],
            "AuthorTime": track_info["author_time"],
            "Authors": [{"UserId": id, "Name": None} for id in track_info["tmx_author_id"]]
        }
    return selected_tracks

def construct_project_map_rows(uids: list, project_slug: str):
    return [{"map_uid": uid, "project_slug": project_slug} for uid in uids]