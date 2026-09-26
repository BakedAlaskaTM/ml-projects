import json
import io
from datetime import datetime, timezone
from pygbx import Gbx, GbxType

def parse_tmx_content(results: list, map_uid: str, identities: list[dict], seen_identities: set) -> list[dict]:
    output = []
    for rec in results:
        if rec["Position"] == None:
            continue
        clean_replay_at = rec["ReplayAt"].split(".")[0]
        dt = datetime.strptime(clean_replay_at, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        output.append({
            "time": rec["ReplayTime"],
            "leaderboard": "TMX",
            "driven_on": dt.isoformat(),
            "player_identity_id": rec["User"]["UserId"],
            "map_uid": map_uid
        })
        if rec["User"]["UserId"] not in seen_identities:
            identities.append({"provider": "TMX", "username": rec["User"]["Name"], "external_id": rec["User"]["UserId"]})
            seen_identities.add(rec["User"]["UserId"])
    return output

def parse_dedi_content(content: str, map_uid: str, identities: list[dict], seen_identities: set) -> list[dict]:
    output = []
    rows = content.split("\r\n")
    count = 0
    for row in range(1, len(rows)):
        if count == 10:
            return output
        rec = rows[row].split(",")
        if len(rec) < 8:
            continue
        output.append({
            "time": int(rec[1]),
            "leaderboard": "DEDIMANIA",
            "driven_on": unix_to_timestamptz(int(rec[3])),
            "player_identity_id": rec[4][4:],
            "map_uid": map_uid
        })
        if rec[4][4:] not in seen_identities:
            identities.append({"provider": "DEDIMANIA", "username": rec[6], "external_id": rec[4][4:]})
            seen_identities.add(rec[4][4:])
        count += 1
    return output

def unix_to_timestamptz(unix: str):
    return datetime.strftime(datetime.fromtimestamp(unix), "%Y-%m-%dT%H:%M:%S")

def write_json(filename: str, data):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=True)

def read_json(filename):
    try:
        file = open(filename, "r")
    except FileNotFoundError:
        print(f"FileNotFoundError: File '{filename}' does not exist.")
        return None
    else:
        file_str = file.read()
        file.close()
    return json.loads(file_str)

def process_replay(content: bytes):
    g = Gbx(io.BytesIO(content))
    try:
        replay = g.get_class_by_id(GbxType.REPLAY_RECORD)
        _ = replay.track
    except AttributeError:
        replay = g.get_class_by_id(GbxType.REPLAY_RECORD_OLD)
        _ = replay.track
    return replay.driver_login

def parse_external_id(id_str: str, provider: str):
    if provider == "TMX":
        return int(id_str)
    return id_str

def construct_profile_graph(profiles: list[dict], user_ids: list[dict]) -> dict:
    graph = {parse_external_id(id["external_id"], id["provider"]): set() for id in user_ids}

    for profile in profiles:
        linked_identities = profile["MatchedIdentity"]
        for i in range(len(linked_identities)):
            target_id = linked_identities[i]
            graph[parse_external_id(target_id["external_id"], target_id["provider"])] = set([parse_external_id(identity["external_id"], identity["provider"]) for identity in linked_identities if identity["external_id"] != target_id["external_id"]])

    return graph