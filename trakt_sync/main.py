import argparse
import os
import json
from .auth import authenticate
from .api import TraktAPI
from .parser import parse_csv

def get_file_path(base_dir, filename):
    return os.path.join(base_dir, filename)

def find_default_data_dir():
    # Look for directory starting with 'letterboxd-' in current dir
    for item in os.listdir('.'):
        if os.path.isdir(item) and item.startswith('letterboxd-'):
            return item
    return None

def get_input(prompt, default=None):
    if default:
        user_input = input(f"{prompt} [{default}]: ")
        return user_input.strip() or default
    else:
        return input(f"{prompt}: ").strip()

CREDENTIALS_FILE = "credentials.json"

def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def save_credentials(client_id, client_secret):
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump({"client_id": client_id, "client_secret": client_secret}, f)

def main():
    parser = argparse.ArgumentParser(description="Sync Letterboxd export to Trakt")
    parser.add_argument("--client-id", help="Trakt Client ID")
    parser.add_argument("--client-secret", help="Trakt Client Secret")
    parser.add_argument("--data-dir", help="Path to Letterboxd export directory")
    parser.add_argument("--sync", choices=['watchlist', 'ratings', 'watched', 'likes', 'all', 'clean'], default='all', help="What to sync (or clean)")
    parser.add_argument("--list-name", help="Name of the Trakt list for Likes")
    parser.add_argument("--no-input", action="store_true", help="Disable interactive prompts")
    
    args = parser.parse_args()

    # 1. Credentials
    c_id = args.client_id or os.environ.get("TRAKT_CLIENT_ID")
    c_secret = args.client_secret or os.environ.get("TRAKT_CLIENT_SECRET")
    
    # Try loading from file if not provided
    if not c_id: 
        saved_creds = load_credentials()
        if saved_creds:
            if not args.no_input:
                use_saved = get_input("Found saved credentials. Use them? [Y/n]", "Y")
                if use_saved.lower() == 'y':
                    c_id = saved_creds.get("client_id")
                    c_secret = saved_creds.get("client_secret")
                else:
                    # User explicitly said no, maybe we should delete them? 
                    # The prompt implied "deleting cache", so let's delete if they say no.
                    if os.path.exists(CREDENTIALS_FILE):
                        os.remove(CREDENTIALS_FILE)
                        print("Saved credentials deleted.")
            else:
                 # In non-interactive mode, use them if available and no args provided
                 c_id = saved_creds.get("client_id")
                 c_secret = saved_creds.get("client_secret")

    if not args.no_input:
        if not c_id:
            c_id = get_input("Trakt Client ID")
        if not c_secret:
            c_secret = get_input("Trakt Client Secret")
            
    if not c_id or not c_secret:
        print("Error: Client ID and Secret are required.")
        return
        
    # Save credentials if they work? Or just save them now? 
    # Let's save them now. Validating them happens during auth.
    if not args.no_input: # Only save if we are in interactive mode (presumably)
        # Check if we should save. If we just loaded them, no need to re-save.
        # But simple logic: just save.
        save_credentials(c_id, c_secret)

    # 2. Authentication
    print("Authenticating...")
    try:
        token = authenticate(c_id, c_secret)
    except Exception as e:
        print(f"Authentication failed: {e}")
        return
        
    api = TraktAPI(token, c_id)

    # 3. Clean Account
    if args.sync == 'clean':
        print("\n!!! WARNING: YOU ARE ABOUT TO DELETE DATA FROM YOUR TRAKT ACCOUNT !!!")
        print("This will remove all items from your Watchlist, Ratings, Watched History, and the Favorites list.")
        
        if not args.no_input:
            confirmation = get_input("Type 'DELETE_EVERYTHING' to confirm")
            if confirmation != "DELETE_EVERYTHING":
                print("Confirmation failed. Aborting.")
                return
        
        print("Proceeding with account cleanup...")
        
        # 1. Watchlist
        print("Fetching Watchlist...")
        watchlist = api.get_watchlist()
        if watchlist:
            print(f"Found {len(watchlist)} items in Watchlist. removing...")
            api.remove_from_watchlist(watchlist)
        else:
            print("Watchlist is empty.")
            
        # 2. Ratings
        print("Fetching Ratings...")
        ratings = api.get_ratings()
        if ratings:
            print(f"Found {len(ratings)} ratings. removing...")
            api.remove_ratings(ratings)
        else:
            print("No ratings found.")
            
        # 3. History
        print("Fetching History...")
        history = api.get_history()
        # History is a list of objects, we need to handle pagination potentially, 
        # but for now we rely on the large limit.
        if history:
            print(f"Found {len(history)} history items. removing...")
            api.remove_history(history)
        else:
            print("No history found.")
            
        # 4. Lists (Favorites)
        # Ask for list name again or iterate all? Let's just do Favorites for now as per plan.
        # But maybe we should search for the list by name?
        user_lists = api.get_user_lists()
        target_list_name = args.list_name
        if not args.no_input and not args.list_name:
             target_list_name = get_input("Trakt List Name to delete", "Favorites")
        
        if not target_list_name:
             target_list_name = "Favorites"
             
        target_list = next((l for l in user_lists if l['name'] == target_list_name), None)
        if target_list:
             print(f"Deleting list '{target_list_name}'...")
             api.delete_list(target_list['ids']['trakt'])
        else:
             print(f"List '{target_list_name}' not found.")
             
        print("Cleanup complete.")
        return

    # 4. Data Directory
    data_dir = args.data_dir
    if not data_dir:
        default_dir = find_default_data_dir()
        if not args.no_input:
            data_dir = get_input("Letterboxd Data Directory", default_dir)
        else:
            data_dir = default_dir
            
    if not data_dir or not os.path.exists(data_dir):
        print(f"Error: Data directory '{data_dir}' not found.")
        return

    # 5. Likes List Name
    list_name = args.list_name
    if args.sync in ['likes', 'all']:
        if not list_name and not args.no_input:
            list_name = get_input("Trakt List Name for Likes", "Favorites")
        if not list_name:
            list_name = "Favorites"

    # Execution
    if args.sync in ['watchlist', 'all']:
        path = get_file_path(data_dir, "watchlist.csv")
        if os.path.exists(path):
            print(f"Reading {path}...")
            movies = list(parse_csv(path, 'watchlist'))
            print(f"Found {len(movies)} movies in watchlist.")
            api.sync_watchlist(movies)
        else:
            print(f"Warning: {path} not found.")

    if args.sync in ['ratings', 'all']:
        path = get_file_path(data_dir, "ratings.csv")
        if os.path.exists(path):
            print(f"Reading {path}...")
            movies = list(parse_csv(path, 'ratings'))
            print(f"Found {len(movies)} ratings.")
            api.sync_ratings(movies)
        else:
            print(f"Warning: {path} not found.")

    if args.sync in ['watched', 'all']:
        path = get_file_path(data_dir, "watched.csv")
        if os.path.exists(path):
            print(f"Reading {path}...")
            movies = list(parse_csv(path, 'watched'))
            print(f"Found {len(movies)} watched movies.")
            api.sync_history(movies)
        else:
            print(f"Warning: {path} not found.")

    if args.sync in ['likes', 'all']:
        path = get_file_path(data_dir, "likes/films.csv")
        if os.path.exists(path):
            print(f"Reading {path}...")
            movies = list(parse_csv(path, 'likes'))
            print(f"Found {len(movies)} liked movies.")
            api.sync_likes_to_list(movies, list_name=list_name)
        else:
            print(f"Warning: {path} not found.")

    print("Done!")

if __name__ == "__main__":
    main()
