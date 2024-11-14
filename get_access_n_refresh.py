import spotipy
from spotipy.oauth2 import SpotifyOAuth
import webbrowser
import os
import json

# Set your Spotify credentials
SPOTIFY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"

SCOPE = 'user-library-read user-read-private'  # Add necessary scope

# Initialize Spotipy's OAuth handler
sp_oauth = SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                        client_secret=SPOTIFY_CLIENT_SECRET,
                        redirect_uri=SPOTIFY_REDIRECT_URI,
                        scope=SCOPE)

# Function to retrieve the refresh token and access token after initial authorization
def get_initial_tokens():
    # Get the authorization URL and prompt user to login
    auth_url = sp_oauth.get_authorize_url()
    print(f"Please go to this URL and log in: {auth_url}")
    webbrowser.open(auth_url)

    # Get the redirect URL after authorization
    redirect_response = input("Paste the URL you were redirected to here: ")

    try:
        # Retrieve tokens from authorization code
        token_info = sp_oauth.get_access_token(redirect_response)
        access_token = token_info['access_token']
        refresh_token = token_info['refresh_token']

        # Save both tokens for future use
        with open('tokens.json', 'w') as file:
            json.dump(token_info, file)
        
        print("Tokens saved successfully.")
        return token_info
    except spotipy.oauth2.SpotifyOauthError as e:
        print(f"Error during initial token retrieval: {e}")
        return None

# Function to refresh the access token using the saved refresh token
def refresh_access_token():
    # Load saved tokens
    try:
        with open('tokens.json', 'r') as file:
            token_info = json.load(file)
            refresh_token = token_info['refresh_token']
    except (FileNotFoundError, KeyError):
        print("Tokens not found. Initiating authorization process.")
        return get_initial_tokens()

    # Refresh access token using refresh token
    try:
        refreshed_token_info = sp_oauth.refresh_access_token(refresh_token)
        
        # Update and save the refreshed token info
        with open('tokens.json', 'w') as file:
            json.dump(refreshed_token_info, file)
        
        print("Access token refreshed and saved successfully.")
        return refreshed_token_info
    except spotipy.oauth2.SpotifyOauthError as e:
        print(f"Error while refreshing access token: {e}")
        print("Re-authorization needed.")
        return get_initial_tokens()

# Main function to get valid tokens
def main():
    # Attempt to refresh the access token
    token_info = refresh_access_token()
    if token_info:
        print(f"Access Token: {token_info['access_token']}")
        print(f"Refresh Token: {token_info.get('refresh_token', 'Refresh token unavailable')}")
    else:
        print("Failed to obtain tokens.")

# Run the main function
if __name__ == "__main__":
    main()
