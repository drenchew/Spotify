import os
import json
import boto3
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Environment variables for Lambda configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
SPOTIFY_SCOPE = 'user-read-recently-played'



#get refresh token from dynamodb table
def get_refresh_token():
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')

    table = dynamodb.Table('SpotifyTokens')
    response = table.get_item(Key={'user_id': '313i5r4qvscyutkcnuaq5e257d4i'})
    item = response.get('Item')
    return item['token_data']




# if token is expired, refresh it
def refresh_token(token_info):
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPE
    )
    token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

#save new refresh token to the dynamodb table
def save_refresh_token(token_info):
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
    table = dynamodb.Table('SpotifyTokens')
    tableWithData = dynamodb.Table('SpotifyListeningHistory')
    users = tableWithData.scan()
    for user in users['Items']:
        table.put_item(Item={ 'user_id': user['user_id'], 'token_data': token_info })
        
    table.put_item(Item={
        'user_id': '313i5r4qvscyutkcnuaq5e257d4i',
        'token_data': token_info
    })




def get_spotify_client():
    # Configure Spotipy's OAuth manager
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPE
    )

    # load token info from dynamodb
    token_info = get_refresh_token()


    # If token is missing or expired, refresh it
    if token_info and sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    elif not token_info:
        # Initial authorization flow, needs user login
        auth_url = sp_oauth.get_authorize_url()
        print(f"Please authorize the app by visiting: {auth_url}")
        # Wait for authorization code, then get the token
        # This part is tricky in Lambda; use an external process or initial setup script
        return None

    # Save the new token info
    save_refresh_token(token_info)

    
    # Initialize Spotipy client
    sp = spotipy.Spotify(auth=token_info['access_token'])
    return sp

def get_recently_played_tracks():
    sp = get_spotify_client()
    if not sp:
        print("Spotify client initialization failed. Authorization required.")
        return []

    # Get recently played tracks
    results = sp.current_user_recently_played(limit=50)
    tracks = []

    for item in results['items']:
        track = item['track']
        played_at = item['played_at']
        track_info = {
            'track_name': track['name'],
            'artist_name': track['artists'][0]['name'],
            'album_name': track['album']['name'],
            'played_at': played_at
        }
        tracks.append(track_info)

    return tracks

def lambda_handler(event, context):
    # Main Lambda handler to get and print recently played tracks
    tracks = get_recently_played_tracks()
    if tracks:
        print(f"Retrieved {len(tracks)} tracks:")
        for track in tracks:
            print(track)
    else:
        print("No recently played tracks found or Spotify client could not be initialized.")

    return {
        'statusCode': 200,
        'body': json.dumps({'tracks': tracks})
    }


def write_to_dynamodb():
    dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
    table = dynamodb.Table('SpotifyTokens')
    token_data = {
        'access_token': 'example_access_token',
        'refresh_token': 'example_refresh_token',
        'expires_in': 3600
    }
    table.put_item(Item={
        'user_id': '313i5r4qvscyutkcnuaq5e257d4i',
        'token_data': json.dumps(token_data)  # Convert token_data to a JSON string
    })

def read_from_dynamodb():
    dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
    table = dynamodb.Table('SpotifyTokens')
    response = table.get_item(Key={
        'user_id': '313i5r4qvscyutkcnuaq5e257d4i',
        'token_data': json.dumps({
            'access_token': 'test access_token',
            'refresh_token': 'tesr refresh_token',
            'expires_in': 3600
        })  # Ensure the sort key matches the stored item
    })
    item = response.get('Item')
    if item:
        print(item)
    else:
        print("No item found with the specified key.")

def read_all_users():
    dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
    table = dynamodb.Table('SpotifyTokens')
    response = table.scan()
    items = response.get('Items', [])

    # check for each user when the token expires
    for item in items:
        token_data = item['token_data']
        print(f"User: {item['user_id']}, Expires in: {token_data['expires_in']} seconds")


# make a telegram bot that will send a message containing the most streamed song of the week


def get_most_streamed_song_of_the_week():
    sp = get_spotify_client()
    if not sp:
        print("Spotify client initialization failed. Authorization required.")
        return []

    # Get the current user's top tracks
    results = sp.current_user_top_tracks(time_range='short_term', limit=1)
    track = results['items'][0]
    track_info = {
        'track_name': track['name'],
        'artist_name': track['artists'][0]['name'],
        'album_name': track['album']['name'],
        'popularity': track['popularity']
    }

    return track_info

#save the most streamed song of the week  for all users to dynamodb
def save_most_streamed_song_of_the_week():
    dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
    table = dynamodb.Table('MostStreamedSongs')
    song_info = get_most_streamed_song_of_the_week()
    table.put_item(
        Item={
            'user_id': '313i5r4qvscyutkcnuaq5e257d4i',
            'song_data': {
                'S': song_info['track_name'],
                'A': song_info['artist_name'],
                'B': song_info['album_name'],
                'N': str(song_info['popularity'])
            }
        }
    )
    print(f"Song '{song_info['track_name']}' saved for user 313i5r4qvscyutkcnuaq5e257d4i")


# Run the Lambda handler
if __name__ == "__main__":

    #write_to_dynamodb()
    read_all_users()
    #read_from_dynamodb()

    #lambda_handler({}, {})  