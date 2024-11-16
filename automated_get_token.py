import requests
import urllib.parse
import os
from flask import Flask, request, redirect

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

# Flask app for handling redirect
app = Flask(__name__)

@app.route("/")
def index():
    return f'<a href="{auth_url}" target="_blank">Click here to authorize Spotify access</a>'

@app.route("/callback")
def callback():
    # Extract authorization code
    code = request.args.get("code")
    if not code:
        return "Error: Authorization code not found in the callback URL.", 400

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

        return (
            f"<h1>Authorization Successful!</h1>"
            f"<p>Access Token: {access_token}</p>"
            f"<p>Refresh Token: {refresh_token}</p>"
            f"<p>Expires In: {expires_in} seconds</p>"
        )
    else:
        return f"Error retrieving tokens: {response.status_code}<br>{response.text}", 400

if __name__ == "__main__":
    print(f"Please go to http://localhost:8888 to authorize access.")
    app.run(port=8888)
