import requests
import json
import os
import webbrowser
from typing import Optional

TOKEN_FILE = "token.json"
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"

def get_authorization_url(client_id: str) -> str:
    base_url = "https://trakt.tv/oauth/authorize"
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
    }
    return f"{base_url}?{'&'.join([f'{key}={val}' for key, val in params.items()])}"

def get_access_token(client_id: str, client_secret: str, auth_code: str) -> str:
    token_url = "https://api.trakt.tv/oauth/token"
    payload = {
        "code": auth_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    response = requests.post(token_url, json=payload)
    if response.status_code == 200:
        data = response.json()
        with open(TOKEN_FILE, 'w') as f:
            json.dump(data, f)
        return data["access_token"]
    else:
        raise Exception(f"Error obtaining access token: {response.text}")

def authenticate(client_id: str, client_secret: str) -> str:
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                data = json.load(f)
                return data["access_token"]
        except (json.JSONDecodeError, KeyError):
            pass
            
    auth_url = get_authorization_url(client_id)
    print(f"Please go to: {auth_url}")
    webbrowser.open(auth_url)
    
    code = input("Enter the code from Trakt: ")
    return get_access_token(client_id, client_secret, code)
