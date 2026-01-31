import os
import sys
# Add current directory to path to allow importing trakt_sync
sys.path.append(os.getcwd())

from trakt_sync.parser import parse_csv

def find_data_dir():
    for item in os.listdir('.'):
        if os.path.isdir(item) and item.startswith('letterboxd-'):
            return item
    return None

def test_parsing():
    data_dir = find_data_dir()
    if not data_dir:
        print("Error: No 'letterboxd-*' directory found.")
        return

    print(f"Using data directory: {data_dir}")

    print("Testing Watchlist...")
    path = os.path.join(data_dir, "watchlist.csv")
    if os.path.exists(path):
        movies = list(parse_csv(path, 'watchlist'))
        print(f"Parsed {len(movies)} movies.")
        if len(movies) > 0:
            print(f"Sample: {movies[0]}")
    else:
        print("watchlist.csv not found")
    
    print("\nTesting Ratings...")
    path = os.path.join(data_dir, "ratings.csv")
    if os.path.exists(path):
        movies = list(parse_csv(path, 'ratings'))
        print(f"Parsed {len(movies)} ratings.")
        if len(movies) > 0:
            print(f"Sample: {movies[0]}")
    else:
        print("ratings.csv not found")
        
    print("\nTesting Watched...")
    path = os.path.join(data_dir, "watched.csv")
    if os.path.exists(path):
        movies = list(parse_csv(path, 'watched'))
        print(f"Parsed {len(movies)} watched items.")
        if len(movies) > 0:
            print(f"Sample: {movies[0]}")
    else:
        print("watched.csv not found")

    print("\nTesting Likes...")
    path = os.path.join(data_dir, "likes/films.csv")
    if os.path.exists(path):
        movies = list(parse_csv(path, 'likes'))
        print(f"Parsed {len(movies)} liked items.")
        if len(movies) > 0:
            print(f"Sample: {movies[0]}")
    else:
        print("likes/films.csv not found")

if __name__ == "__main__":
    test_parsing()
