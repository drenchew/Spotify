import os
import json
import boto3
import spotipy
from spotipy.oauth2 import SpotifyOAuth

import time

# Environment variables for Lambda configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
SPOTIFY_SCOPE = 'user-read-recently-played user-top-read'

# DynamoDB tables
dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
tokens_table = dynamodb.Table('token-refs')
songs_table = dynamodb.Table('SpotifyListeningHistory')

class Token:

    def __init__(self, user_id, access,refresh, expires_at):
        self.dict = {'user_id': user_id, 'access_token': access, 'refresh_token': refresh, 'expires_at': expires_at}

    def __repr__(self):
        return f"Token(user_id={self.user_id}, token_data={self.token_data})"

    def __str__(self):
        return self.__repr__()

# Get refresh token for a user from DynamoDB
def get_user_token2(user_id):
    response = tokens_table.get_item(Key={'user_id': user_id})
    token_obj = Token(
     user_id=response['Item']['user_id'],
     access=response['Item']['access_token'],
     refresh=response['Item']['refresh_token'],
     expires_at=int(response['Item']['expires_at'])
   )

    return token_obj

def get_user_token(user_id):
    response = tokens_table.get_item(Key={'user_id': user_id})
   # print(response)


    token_data = response.get('Item', {})
    #print(token_data)
    
    #token_data['expires_at'] = int(token_data['expires_at'])

    print(token_data['user_id'])


    return token_data

# Refresh access token if expired
def refresh_token(token_info):
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPE
    )
    refreshed_token_info = sp_oauth.refresh_access_token(token_info.dict['refresh_token'])
    return refreshed_token_info

# Save updated token data to DynamoDB for a user
#and delete the old one
def save_user_token(user_id, token_info):
    tokens_table.put_item(Item={'user_id': user_id, 'token_data': token_info})
    #check which token is the newest


# Initialize Spotify client for a user
def get_spotify_client(user_id):
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPE
    )

    token_info = get_user_token2(user_id)
   # token_info = json.loads(token_info) if token_info else None
    print("sdsd")
    

    print(token_info.dict['expires_at'])

    now = int(time.time())
    delta =token_info.dict["expires_at"] - now
    print(delta)
   
    if token_info and sp_oauth.is_token_expired(token_info.dict):
        token_info = refresh_token(token_info)
        save_user_token(user_id, token_info)
    elif not token_info:
        print(f"No token found for user {user_id}. Authorization required.")
        return None

    return spotipy.Spotify(auth=token_info['access_token'])

# Retrieve and save the most streamed song of the week for a user
def save_most_streamed_song(user_id):
    sp = get_spotify_client(user_id)
    if not sp:
        return

    results = sp.current_user_top_tracks(time_range='short_term', limit=1)
    if results['items']:
        track = results['items'][0]
        song_info = {
            'user_id': user_id,
            'plated_at': track['played_at'],
            'track_name': track['name'],
            'artist_name': track['artists'][0]['name'],
            'album_name': track['album']['name'],
            'popularity': track['popularity']
        }

        songs_table.put_item(Item=song_info)
        print(f"Saved song '{track['name']}' for user {user_id}")

# Retrieve all users' most streamed song of the week and save to DynamoDB
def save_all_users_top_tracks():
    response = tokens_table.scan()
    for item in response.get('Items', []):
        user_id = item['user_id']
        save_most_streamed_song(user_id)

# Main Lambda handler
def lambda_handler(event, context):
    save_all_users_top_tracks()
    return {
        'statusCode': 200,
        'body': json.dumps("Saved most-streamed songs for all users.")
    }

# To test locally
if __name__ == "__main__":
    print(lambda_handler({}, {}))
