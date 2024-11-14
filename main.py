import json
import os
import boto3
import requests
import logging
import base64
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from datetime import datetime  # Correctly import datetime

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_REGION_NAME = os.environ['AWS_REGION_NAME']
AWS_DYNAMODB_TABLE_NAME = os.environ['AWS_DYNAMODB_TABLE_NAME']
SPOTIFY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']

# Initialize DynamoDB client
client = boto3.client('dynamodb', region_name=AWS_REGION_NAME, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

def get_credentials():
   return "BQBKvMOHXh_SuW0L3r4iEhNrgtqlXD_MffIB8uFcnKzpwbZ8Ijhioyefuo0MAoc8jMfH2uqqO0_b2jt4RNHT-CkaiSqXIDYPUG1_gkv7utlv35JPSRYQ1c8LNU_hHE9G0gA6CPKr2XeveQsrywtXLTtmhQf6Mur-hk8mxHuoKEey28UE5PXzHaTNCIsFUEDxnc8CLmoFzlaq4W3pulYyEt03ZOnAErixRFOut498OYG6"
       
    

def get_playlist(access_token):
    # Fetch a specific playlist's details
    url = 'https://api.spotify.com/v1/playlists/37i9dQZF1DX0XUsuxWHRQd'
    headers = {
        'Authorization': 'Bearer ' + access_token
    }
    response = requests.get(url, headers=headers)
    response = response.json()
    return response

def get_songs(playlist):
    # Extract song details from the playlist
    songs = []
    for item in playlist['tracks']['items']:
        track = item['track']
        song = {
            'song_id': track['id'],
            'song_name': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'release_date': track['album']['release_date'],
            'duration': track['duration_ms'],
            'popularity': track['popularity']
        }
        songs.append(song)
    return songs

def save_songs(songs, user_id):
    # Save each song to DynamoDB with the user_id
    for song in songs:
        played_at = datetime.utcnow().isoformat()
        response = client.put_item(
            TableName=AWS_DYNAMODB_TABLE_NAME,
            Item={
                'user_id': {
                    'S': user_id
                },
                'played_at': {'S': played_at},  # Ensure played_at is included
                'song_id': {
                    'S': song['song_id']
                },
                'song_name': {
                    'S': song['song_name']
                },
                'artist': {
                    'S': song['artist']
                },
                'album': {
                    'S': song['album']
                },
                'release_date': {
                    'S': song['release_date']
                },
                'duration': {
                    'N': str(song['duration'])
                },
                'popularity': {
                    'N': str(song['popularity'])
                }
            }
        )
        logger.info(f"Song '{song['song_name']}' saved for user {user_id}")
    return

def get_user_id(access_token):
    # Fetch the user's profile details
    url = 'https://api.spotify.com/v1/me'
    headers = {
        'Authorization': 'Bearer ' + access_token
    }
    response = requests.get(url, headers=headers)
    response = response.json()
    return response['id']

def lambda_handler(event, context):
    access_token = get_credentials()
    user_id = get_user_id(access_token)  # Get the actual user ID
    playlist = get_playlist(access_token)
    songs = get_songs(playlist)
    save_songs(songs, user_id)  # Save songs with the actual user ID
    return {
        'statusCode': 200,
        'body': json.dumps('Songs saved')
    }


def last_played_songs():
    SCOPE = 'user-read-recently-played'
    sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri="http://localhost:8888/callback",
    scope=SCOPE)
    token_info = sp_oauth.get_cached_token()

    access_token = "BQBEmZ9MWa-BjuwrWixw4nhRjhfVYxGrFpM3DUJnouGmSIiZc9RJEcQ-KI8yFut69MC3slnaAStaAECZzu1eWE4KSkZ0079fO9Cx6-blqyw-0eVZDvEvGUjG4wwHt2NC2MYyxBkHx-kFvx6xPq4s80WPQVMtPGA2hBGHYcy99P6iJIls3tOXABIsUekBB5vPUYaFhvqzBpWK2h4lLJH23BbxgJB_fPfhO1W0qtuixkU7"
    access_token = "BQBEmZ9MWa-BjuwrWixw4nhRjhfVYxGrFpM3DUJnouGmSIiZc9RJEcQ-KI8yFut69MC3slnaAStaAECZzu1eWE4KSkZ0079fO9Cx6-blqyw-0eVZDvEvGUjG4wwHt2NC2MYyxBkHx-kFvx6xPq4s80WPQVMtPGA2hBGHYcy99P6iJIls3tOXABIsUekBB5vPUYaFhvqzBpWK2h4lLJH23BbxgJB_fPfhO1W0qtuixkU7"
    sp = spotipy.Spotify(auth=access_token)
    results = sp.current_user_recently_played(limit=10)
    for idx, item in enumerate(results['items']):
        track = item['track']
        print(idx, track['artists'][0]['name'], " - ", track['name'])




# Run the Lambda function locally
if __name__ == '__main__':
  #  lambda_handler(None, None)

    dynamodb = boto3.client('dynamodb', region_name='eu-north-1')
    response = dynamodb.scan(TableName='SpotifyListeningHistory')


    last_played_songs()

    # Print the results
    #for item in response['Items']:
     #   print(item['song_name']['S']) 
