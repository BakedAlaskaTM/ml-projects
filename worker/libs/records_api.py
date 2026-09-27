from concurrent.futures import ThreadPoolExecutor
from requests import Session, exceptions
from .utils import parse_tmx_content, parse_dedi_content, process_replay
from functools import partial
import time
import random

def fetch_tmx(track: dict, session: Session):
    response = session.get(f"https://tmnf.exchange/api/replays?trackId={track['tmx_id']}&count=10&fields=User.UserId%2CUser.Name%2CReplayTime%2CReplayAt%2CPosition")
    if response.status_code != 200:
        print(f"Error on map {track['name']}")
        return {"track": track, "content": None}
    content = response.json()
    return {"track": track, "content": content}

def update_tmx_recs(session: Session, track_info: list[dict]):
    seen_pids = set()
    recs = []
    identities = []

    fetch_with_session = partial(fetch_tmx, session=session)
    
    with ThreadPoolExecutor(max_workers=8) as exe:
        # map yields dicts directly
        results = exe.map(fetch_with_session, track_info)
        
        # Process results sequentially as they arrive (no need for double iteration)
        for data in results:
            if data["content"] is None:
                continue
            
            # Extract and parse content
            parsed_recs = parse_tmx_content(
                data["content"]["Results"], 
                data["track"]["uid"], 
                identities, 
                seen_pids
            )
            recs.extend(parsed_recs)

    return recs, identities


def update_dedi_recs(session: Session, track_info: list[dict]):
    seen_logins = set()
    recs = []
    identities = []
    for n, track in enumerate(track_info):
        try:
            response = session.get(f"http://dedimania.net:8000/MAP?uid={track['uid']}", timeout=(5, 10))
            if response.status_code != 200:
                print(f"Error on map {track['name']}")
                continue
        except (exceptions.ReadTimeout, exceptions.ConnectTimeout):
            print(f"Timeout: Dedimania API took too long to respond for map {track['uid']}")
        except exceptions.RequestException as e:
            print(f"Connection failed for map {track['uid']}: {e}")
        else:
            content = response.content.decode("utf-8")
            parsed_recs = parse_dedi_content(content, track['uid'], identities, seen_logins)
            recs.extend(parsed_recs)
            print(n)
            time.sleep(2.5)
    return recs, identities

def get_sample_replays(session: Session, user_ids: list[int], fetch_count: int = 100, sample_size: int = 20):
    sample_ids = []
    fetch_with_session = partial(fetch_user, session, fetch_count=fetch_count)
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = executor.map(fetch_with_session, user_ids)

        for user_id, content in results:
            if content is None:
                print("Broke")
                continue

            ids = [(r["ReplayId"], user_id) for r in content]
            sample_ids.extend(random.sample(ids, sample_size) if len(ids) > sample_size else ids)
    return sample_ids

def find_logins(session: Session, sample_pairs: list[tuple[int, int]]) -> list[tuple[str, str]]:
    """
    Return structure is {(tmx_id, login), ...}
    """
    logins = set()
    fetch_with_session = partial(fetch_replay, session)
    with ThreadPoolExecutor(max_workers=8) as executor:
        
        results = executor.map(fetch_with_session, sample_pairs)

        for id_pair, content in results:
            if content is None:
                print(f"Dead on {id_pair[1]}: {id_pair[0]}")
                continue

            logins.add((id_pair[1], process_replay(content)))
    return list(logins)

def fetch_replay(session: Session, id_pair: tuple[int, int]):
    """
    id_pair looks like (replay_id, user_id)
    """
    url = f"https://tmnf.exchange/recordgbx/{id_pair[0]}"
    try:
        r = session.get(url, timeout=10)
        if r.status_code == 200:
            return id_pair, r.content
    except Exception:
        pass
    return id_pair, None

def fetch_user(session: Session, user_id: int, fetch_count: int = 100):
    url = f"https://tmnf.exchange/api/replays?userId={user_id}&count={fetch_count}&fields=ReplayId"
    try:
        r = session.get(url, timeout=10)
        if r.status_code == 200:
            return user_id, r.json()["Results"]
    except Exception:
        pass
    return user_id, None
