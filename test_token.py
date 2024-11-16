import requests
import boto3
import urllib.parse
import  os

# Replace these with your Spotify Developer App credentials
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8888/callback'

# Full scope for maximum permissions
SCOPE = "ugc-image-upload user-read-recently-played user-top-read user-read-playback-position user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-modify-public playlist-modify-private playlist-read-private playlist-read-collaborative app-remote-control streaming user-follow-modify user-follow-read user-library-modify user-library-read user-read-email user-read-private"

# Spotify Authorization URL
auth_url = (
    f"https://accounts.spotify.com/authorize?client_id={CLIENT_ID}"
    f"&response_type=code&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    f"&scope={urllib.parse.quote(SCOPE)}"
)
print(f"Please go to this URL and authorize access:\n{auth_url}")

# After authorization, enter the redirected URL
redirected_url = input("Paste the redirected URL here: ")

# Extract the authorization code from the redirected URL
parsed_url = urllib.parse.urlparse(redirected_url)
code = urllib.parse.parse_qs(parsed_url.query).get("code", [None])[0]

if not code:
    print("Error: Authorization code not found in the URL.")
    exit()

# Exchange Authorization Code for Tokens
token_url = "https://accounts.spotify.com/api/token"
headers = {"Content-Type": "application/x-www-form-urlencoded"}
payload = {
    "grant_type": "authorization_code",
    "code": code,
    "redirect_uri": REDIRECT_URI,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
}

response = requests.post(token_url, headers=headers, data=payload)

if response.status_code == 200:
    token_info = response.json()
    access_token = token_info.get("access_token")
    refresh_token = token_info.get("refresh_token")
    expires_in = token_info.get("expires_in")  # Token lifetime in seconds

    print(f"Access Token: {access_token}")
    print(f"Refresh Token: {refresh_token}")
    print(f"Expires In: {expires_in} seconds")
else:
    print(f"Error retrieving tokens: {response.status_code}")
    print(f"Response: {response.text}")

# If only a refresh_token is available, use it to get a new access_token
if not access_token and refresh_token:
    print("Only refresh token available. Attempting to retrieve access token...")
    refresh_payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    refresh_response = requests.post(token_url, headers=headers, data=refresh_payload)
    if refresh_response.status_code == 200:
        refreshed_token_info = refresh_response.json()
        access_token = refreshed_token_info.get("access_token")
        expires_in = refreshed_token_info.get("expires_in")
        print(f"New Access Token: {access_token}")
        print(f"Expires In: {expires_in} seconds")
    else:
        print(f"Error refreshing access token: {refresh_response.status_code}")
        print(f"Response: {refresh_response.text}")
