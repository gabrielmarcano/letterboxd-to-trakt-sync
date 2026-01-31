import requests
import time
from typing import List, Dict, Any
from .models import Movie

class TraktAPI:
    def __init__(self, access_token: str, client_id: str):
        self.base_url = "https://api.trakt.tv"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "trakt-api-version": "2",
            "trakt-api-key": client_id,
        }
        
    def _post(self, endpoint: str, payload: Dict[str, Any], retries: int = 5):
        url = f"{self.base_url}{endpoint}"
        attempt = 0
        while attempt < retries:
            response = requests.post(url, headers=self.headers, json=payload)
            if response.status_code in (200, 201):
                return response.json()
            elif response.status_code == 429:
                print("Rate limited, waiting 5 seconds...")
                time.sleep(5)
                attempt += 1
            else:
                print(f"Error {response.status_code}: {response.text}")
                return None
                
    def _get(self, endpoint: str):
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return None

    def sync_watchlist(self, movies: List[Movie]):
        chunk_size = 100
        for i in range(0, len(movies), chunk_size):
            chunk = movies[i:i + chunk_size]
            payload = {
                "movies": [{"title": m.title, "year": m.year} for m in chunk]
            }
            print(f"Syncing watchlist chunk {i//chunk_size + 1}...")
            self._post("/sync/watchlist", payload)

    def sync_ratings(self, movies: List[Movie]):
        chunk_size = 100
        for i in range(0, len(movies), chunk_size):
            chunk = movies[i:i + chunk_size]
            payload = {
                "movies": [{
                    "title": m.title, 
                    "year": m.year, 
                    "rating": int(m.rating * 2) if m.rating else None, # Trakt uses 1-10
                    "rated_at": m.watched_at # Use watched date as rated date if available approximation
                } for m in chunk if m.rating]
            }
            if not payload["movies"]: continue
            print(f"Syncing ratings chunk {i//chunk_size + 1}...")
            self._post("/sync/ratings", payload)

    def sync_history(self, movies: List[Movie]):
        chunk_size = 100
        for i in range(0, len(movies), chunk_size):
            chunk = movies[i:i + chunk_size]
            # Group by movie to avoid duplicates in payload? 
            # Ideally each history entry is unique. 
            # Trakt history sync is add-only.
            payload = {
                "movies": [{
                    "title": m.title, 
                    "year": m.year, 
                    "watched_at": f"{m.watched_at}T12:00:00.000Z" if m.watched_at else None
                } for m in chunk if m.watched_at]
            }
            if not payload["movies"]: continue
            print(f"Syncing history chunk {i//chunk_size + 1}...")
            self._post("/sync/history", payload)
            
    def get_user_lists(self):
        return self._get(f"/users/me/lists")

    def create_list(self, name: str):
        payload = {
            "name": name,
            "description": "Imported from Letterboxd",
            "privacy": "public",
            "allow_comments": True,
            "display_numbers": False
        }
        return self._post(f"/users/me/lists", payload)

    def sync_likes_to_list(self, movies: List[Movie], list_name: str = "Favorites"):
        lists = self.get_user_lists()
        target_list = next((l for l in lists if l['name'] == list_name), None)
        
        if not target_list:
            print(f"List '{list_name}' not found, creating...")
            target_list = self.create_list(list_name)
            if not target_list:
                print("Failed to create list.")
                return
        
        list_id = target_list['ids']['trakt']
        
        chunk_size = 100
        for i in range(0, len(movies), chunk_size):
            chunk = movies[i:i + chunk_size]
            payload = {
                "movies": [{"title": m.title, "year": m.year} for m in chunk]
            }
            print(f"Syncing {list_name} chunk {i//chunk_size + 1}...")
            self._post(f"/users/me/lists/{list_id}/items", payload)

    # Retrieval Methods
    def get_watchlist(self):
        return self._get(f"/sync/watchlist")

    def get_ratings(self):
        return self._get(f"/sync/ratings")
        
    def get_history(self):
        # History can be huge, pagination might be needed. 
        # For now, let's grab a large limit.
        return self._get(f"/sync/history?limit=10000") 

    # Removal Methods
    def _prepare_remove_payload(self, items: List[Dict]) -> Dict[str, List[Dict]]:
        payload = {"movies": [], "shows": [], "episodes": []}
        for item in items:
            media_type = item.get("type")
            if media_type == "movie" and "movie" in item:
                payload["movies"].append({"ids": item["movie"]["ids"]})
            elif media_type == "show" and "show" in item:
                payload["shows"].append({"ids": item["show"]["ids"]})
            elif media_type == "episode" and "episode" in item:
                payload["episodes"].append({"ids": item["episode"]["ids"]})
            elif media_type == "season" and "season" in item:
                 # Trakt API also supports seasons
                 if "seasons" not in payload: payload["seasons"] = []
                 payload["seasons"].append({"ids": item["season"]["ids"]})
            # Handle cases where type might be missing but keys exist
            elif "movie" in item:
                payload["movies"].append({"ids": item["movie"]["ids"]})
            elif "show" in item:
                payload["shows"].append({"ids": item["show"]["ids"]})
            elif "episode" in item:
                payload["episodes"].append({"ids": item["episode"]["ids"]})
        return payload

    def remove_from_watchlist(self, items: List[Dict]):
        chunk_size = 100
        for i in range(0, len(items), chunk_size):
            chunk = items[i:i + chunk_size]
            payload = self._prepare_remove_payload(chunk)
            if not any(payload.values()): continue
            
            print(f"Removing watchlist chunk {i//chunk_size + 1}...")
            self._post("/sync/watchlist/remove", payload)

    def remove_ratings(self, items: List[Dict]):
        chunk_size = 100
        for i in range(0, len(items), chunk_size):
            chunk = items[i:i + chunk_size]
            payload = self._prepare_remove_payload(chunk)
            if not any(payload.values()): continue
            
            print(f"Removing ratings chunk {i//chunk_size + 1}...")
            self._post("/sync/ratings/remove", payload)

    def remove_history(self, items: List[Dict]):
        chunk_size = 100
        for i in range(0, len(items), chunk_size):
            chunk = items[i:i + chunk_size]
            payload = self._prepare_remove_payload(chunk)
            if not any(payload.values()): continue

            print(f"Removing history chunk {i//chunk_size + 1}...")
            self._post("/sync/history/remove", payload)

    def delete_list(self, list_id: str):
        response = requests.delete(f"{self.base_url}/users/me/lists/{list_id}", headers=self.headers)
        if response.status_code == 204:
            print(f"List {list_id} deleted.")
        else:
            print(f"Failed to delete list {list_id}: {response.status_code}")
