from enum import Enum, auto
import requests

TRACKS_INPUT_PARAMETERS = ["id", "uid", "name", "author", "authoruserid", "replaysby", "count"]
TRACKS_OUTPUT_FIELDS = ["TrackId", "TrackName", "UId", "AuthorTime", "UpdatedAt", "Authors%5B%5D"]
USERS_INPUT_PARAMETERS = ["id", "name"]
USERS_OUTPUT_FIELDS = ["UserId", "Name", "Tracks", "TrackPacks"]

class Category(Enum):
    TRACKS = auto()
    USERS = auto()

def search_tracks(session: requests.Session, query: dict):
    url_base = "https://tmnf.exchange/api/tracks?"
    params = "&".join([f"{param}={value}" for param, value in query.items()])
    params += f"&fields={'%2C'.join(TRACKS_OUTPUT_FIELDS)}"
    response = session.get(f"{url_base}{params}")
    if response.status_code != 200:
        return None
    return response.json()

def search_users(session: requests.Session, query: dict):
    url_base = "https://tmnf.exchange/api/users?"
    return

def search(session: requests.Session, cat: Category, query_str: str | dict):
    query = query_str
    if type(query_str) == str:
        try:
            query = parse_query_string(cat, query_str)
        except SyntaxError:
            print("Invalid query syntax.")
            return None
        
    search_func = None
    match cat:
        case Category.TRACKS: 
            search_func = search_tracks
        case Category.USERS: 
            search_func = search_users
        case _:
            return None

    return search_func(session, query)

def flatten_results(results: list, cat: Category):
    items = []
    if cat == Category.TRACKS:
        for result in results:
            items.append({
                "TrackId": result["TrackId"],
                "TrackName": result["TrackName"],
                "UId": result["UId"],
                "AuthorTime": result["AuthorTime"],
                "UpdatedAt": result["UpdatedAt"],
                "Authors": [{"UserId": author["User"]["UserId"], "Name": author["User"]["Name"]} for author in result["Authors"]]
            })
    return items

def parse_query_string(cat: Category, q_str: str) -> dict:
    """
    Converts a query string in the format input1: value1; input2: value2; input3: value3; etc
    into a dictionary of {input1: value1, input2: value2, input3: value3, etc}
    """
    output = {}
    pairs = q_str.split(";")
    for pair in pairs:
        try:
            param, value = pair.split(":")
        except ValueError:
            raise SyntaxError(f"Invalid input formatting for {pair}.")
        if cat == Category.TRACKS and param.lower() not in TRACKS_INPUT_PARAMETERS:
            raise SyntaxError(f"Invalid parameter {param}.")
        elif cat == Category.USERS and param.lower() not in USERS_INPUT_PARAMETERS:
            raise SyntaxError(f"Invalid parameter {param}.")
        else:
            output[param.strip().lower()] = value.strip().replace(" ", "+")
    return output

if __name__ == "__main__":
    session = requests.Session()
    query_str = input("Track Search: ")
    try:
        results = search(session, Category.TRACKS, query_str)
    except SyntaxError as e:
        print(e)
    else:
        results = flatten_results(results["Results"], Category.TRACKS)
        print(len(results))
    session.close()