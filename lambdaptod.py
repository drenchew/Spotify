import os
import json
import boto3
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time


SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
SPOTIFY_SCOPE = ' '.join([
    'user-library-read',
    'user-library-modify',
    'user-read-playback-state',
    'user-modify-playback-state',
    'user-read-currently-playing',
    'user-read-recently-played',
    'user-top-read',
    'playlist-read-private',
    'playlist-read-collaborative',
    'playlist-modify-public',
    'playlist-modify-private',
    'user-follow-read',
    'user-follow-modify',
    'app-remote-control',
    'streaming',
    'user-read-email',
    'user-read-private'
])


dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
tokens_table = dynamodb.Table('token-refs')
songs_table = dynamodb.Table('SpotifyListeningHistory')

class Token:
    def __init__(self, user_id, access, refresh, expires_at):
        self.dict = {
             'user_id': user_id,
             'access_token': access,
             'refresh_token': refresh,
             'expires_at': expires_at}

    def __repr__(self):
        return f"Token(user_id={self.dict['user_id']}, token_data={self.dict})"


def get_user_token2(user_id):
    response = tokens_table.get_item(Key={'user_id': user_id})
    token_obj = Token(
        user_id=response['Item']['user_id'],
        access=response['Item']['access_token'],
        refresh=response['Item']['refresh_token'],
        expires_at=int(response['Item']['expires_at'])
    )
    return token_obj


def refresh_token(token_info):
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPE
    )
    refreshed_token_info = sp_oauth.refresh_access_token(token_info.dict['refresh_token'])

    print("Refreshed token info:")
    print(refreshed_token_info)

    new_token = Token(user_id=refreshed_token_info['user_id'],
                      access=refreshed_token_info['token_data']['access_token'],
                      refresh=refreshed_token_info['token_data']['refresh_token'],
                      expires_at=refreshed_token_info['token_data']['expires_at'])

    
    token_info.dict.update(new_token)
    return token_info


def save_user_token(user_id, token_info):

    tokens_table.put_item(Item={
        'user_id': user_id,
        'access_token': token_info.dict['access_token'],
        'refresh_token': token_info.dict['refresh_token'],
        'expires_at': token_info.dict['expires_at']})


def get_spotify_client(user_id):
    token_info = get_user_token2(user_id)
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPE
    )

    # Check token expiration and refresh if needed
    now = int(time.time())

    delta = token_info.dict['expires_at'] - now
    print(f"Token expires in {delta} seconds")

    if sp_oauth.is_token_expired(token_info.dict):
        print("Token expired, refreshing...")
        token_info = refresh_token(token_info)
        save_user_token(user_id, token_info)
    elif not token_info:
        print(f"No token found for user {user_id}. Authorization required.")
        return None

    return spotipy.Spotify(auth=token_info.dict['access_token'])


def save_most_streamed_song(user_id):
    sp = get_spotify_client(user_id)
    if not sp:
        return

    try:
        #get current date
        now = int(time.time())
        #transform to YYYY-MM-DD
        now = time.strftime('%Y-%m-%d', time.localtime(now))
        print(now)

        results = sp.current_user_top_tracks(time_range='short_term', limit=1)
        if results['items']:
            track = results['items'][0]
            song_info = {
                'user_id': user_id,
                'played_at': now,
                'track_name': track['name'],
                'artist_name': track['artists'][0]['name'],
                'album_name': track['album']['name'],
            }
            songs_table.put_item(Item=song_info)
            print(f"Saved song '{track['name']}' for user {user_id}")
    except spotipy.exceptions.SpotifyException as e:
        print(f"Error retrieving top track for user {user_id}: {e}")

# Retrieve all users' most streamed song of the last 4 weeks and save to DynamoDB
def save_all_users_top_tracks():
    response = tokens_table.scan()
    for item in response.get('Items', []):
        user_id = item['user_id']
        save_most_streamed_song(user_id)


def lambda_handler(event, context):
    save_all_users_top_tracks()
    return {
        'statusCode': 200,
        'body': json.dumps("Saved most-streamed songs for all users.")
    }

# To test locally
if __name__ == "__main__":
   
    print(lambda_handler({}, {})['statusCode'])
