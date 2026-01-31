# Letterboxd to Trakt Sync

A Python tool to migrate your Letterboxd data (Watchlist, Ratings, Watched
History, and Likes) to Trakt.

## Features

- **Watchlist Sync**: Adds movies to your Trakt Watchlist.
- **Ratings Sync**: Adds ratings to your Trakt account (converting Letterboxd's
  1-5 scale to Trakt's 1-10).
- **Watched History Sync**: Syncs your watched history, preserving the watch
  dates.
- **Likes Sync**: Syncs your liked films to a custom Trakt list named
  "Favorites" (since Trakt doesn't have movie "likes").
- **Account Cleaning**: Feature to remove all data from Trakt, useful for
  restarting a sync.
- **Interactive CLI**: Friendly prompts for credentials, paths, and preferences.
- **Smart Auth**: Saves OAuth token locally so you only need to authenticate
  once.
- **Rate Limit Handling**: Automatically retries requests when Trakt API rate
  limits are hit.

## Prerequisites

- Python 3.6+
- Letterboxd Data Export (CSV files)
- Trakt API Credentials (Client ID and Client Secret). You can get them by
  creating a new API App at [Trakt API Apps](https://trakt.tv/oauth/apps).

## Installation

1. Clone this repository.
2. Ensure you have the required dependencies (standard library `requests` is
   required).
   ```bash
   pip install requests
   ```

## Usage

Run the script using `run.py`.

### 1. Interactive Mode (Recommended)

Just run `python3 run.py`. The script will interactively ask for:

1. **Trakt Credentials**: Client ID and Secret (if not provided via args or
   env).
2. **Letterboxd Data**: It tries to find your unzipped folder automatically
   (e.g., `letterboxd-username-...`) or asks you to confirm the path.
3. **Favorites List Name**: Defaults to "Favorites", but you can choose another
   name for your synced Likes.

```bash
python3 run.py
```

- On the first run, it will open your browser to authenticate with Trakt.
- Paste the code back into the terminal.
- It will save your access token to `token.json` for future runs.

### 2. Batch/Single Command Mode

You can still run fully non-interactively by providing all arguments and adding
`--no-input`:

```bash
python3 run.py --client-id ID --client-secret SECRET --data-dir ./data --sync all --no-input
```

### 3. Sync Specific Items

You can choose what to sync using the `--sync` argument:

**Sync only Watchlist:**

```bash
python3 run.py --sync watchlist
```

**Sync only Ratings:**

```bash
python3 run.py --sync ratings
```

**Sync only Watched History:**

```bash
python3 run.py --sync watched
```

**Sync only Favorites (Likes):**

```bash
python3 run.py --sync likes
```

### 4. Clean Account

⚠️ **WARNING**: This removes all Watchlist items, Ratings, Watched History, and
the Favorites list from your Trakt account.

```bash
python3 run.py --sync clean
```

You will be asked to type `DELETE_EVERYTHING` to confirm.

### 5. Environment Variables

To avoid passing credentials every time, you can set environment variables:

```bash
export TRAKT_CLIENT_ID="your_id"
export TRAKT_CLIENT_SECRET="your_secret"
python3 run.py
```

## structure

- `trakt_sync/`: Main package code.
- `run.py`: Entry point script.
