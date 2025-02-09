import json
import os
import re
import time
from flask_login import current_user
import jwt
import requests
from sqlalchemy import  or_
from sqlalchemy.ext.mutable import MutableDict

from web.lib.av_apis.spotify import  add_tracks_to_spotify_playlist, create_spotify_playlist
from web.model import AppConfig, Playlist, Set, SetBrowsingHistory, SetSearch, Track,Channel
from boilersaas.utils.db import db
from collections import defaultdict

from web.logger import logger

import dotenv

#from web.routes.routes_utils import is_admin
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
dotenv.load_dotenv(dotenv_path)

APPLE_KEY_ID = os.getenv('APPLE_KEY_ID')
APPLE_TEAM_ID = os.getenv('APPLE_TEAM_ID')
APPLE_PRIVATE_KEY = os.getenv('APPLE_PRIVATE_KEY').replace("\\n", "\n")
APPLE_TOKEN_EXPIRY_LENGTH = int(os.getenv('APPLE_TOKEN_EXPIRY_LENGTH'))  # 6 months
    
   

def sanitize_query(query):
    # Trim whitespace, remove any non-alphanumeric characters (excluding spaces), and convert to lowercase
    sanitized_query = re.sub(r'[^a-zA-Z0-9 &]+', '', query).strip().lower()
    return sanitized_query


def error_out(msg):
    return({'error':msg})



        
def compile_and_sort_genres(track_sets):
    genre_counts = defaultdict(int)

    for track_set, track in track_sets:
        for genre in track.genres:
            genre_counts[genre.name] += 1

    sorted_genre_counts = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_genre_counts


def get_browsing_history(user_id, page=1, per_page=20, order_by='recent', search=None):
    # Query to fetch the browsing history for the given user
    query = db.session.query(Set).join(SetBrowsingHistory, Set.id == SetBrowsingHistory.set_id) \
                .join(Channel, Set.channel_id == Channel.id) \
                .filter(SetBrowsingHistory.user_id == user_id) \
                .filter(Set.playable_in_embed == True, Set.published == True, Channel.hidden == False)
    # If there's a search term, apply it to filter the results based on the set's title or channel's author
    if search:
        search_filter = or_(
            Set.title_tsv.match(search),  # Assuming title_tsv is a full-text search vector for the set title
            Set.channel.has(Channel.author.ilike(f'%{search}%'))  # Assuming the author field is searchable
        )
        query = query.filter(search_filter)

    # Ordering based on the order_by parameter
    if order_by == 'recent':
        query = query.order_by(SetBrowsingHistory.datetime.desc())
    elif order_by == 'old':
        query = query.order_by(SetBrowsingHistory.datetime.asc())
    elif order_by == 'views':
        query = query.order_by(Set.view_count.desc())
    elif order_by == 'likes':
        query = query.order_by(Set.like_count.desc())
    
    # Get total results count
    results_count = query.count()

    # Paginate results
    results = query.paginate(page=page, per_page=per_page, error_out=False)

    return results, results_count


                    





    



def spotify_tracks_uris_from_tracks(tracks):    
    return ['spotify:track:'+track['key_track_spotify'] for track in tracks if 'key_track_spotify' in track and track['key_track_spotify']]


def create_spotify_playlist_and_add_tracks(playlist_name, tracks,playlist_id):
    
    
    # check if playlist exists
    playlist = db.session.query(Playlist).filter_by(id=playlist_id,user_id=current_user.id).first()
   
    if not playlist:
        return {"error": "Playlist not found"}
    
    # does this playlist belong to user ?
    if playlist.user_id != current_user.id:
        return {"error": "Unauthorized access to this playlist"}
    

    # does this playlist exist on spotify ?
    
    
    try:
        # Create the Spotify playlist
        new_playlist = create_spotify_playlist(playlist_name)
        if not new_playlist:
            return {"error": "Error creating playlist"}
    except Exception as e:
        return {"error": f"Error creating playlist: {str(e)}"}
    
    
    playlist_id_spotify = new_playlist['id']
    db.session.query(Playlist).filter_by(id=playlist_id,user_id=current_user.id).update({Playlist.playlist_id_spotify: playlist_id_spotify})
    db.session.commit()
    try:
        # Extract track IDs
        track_ids = [track['key_track_spotify'] for track in tracks if 'key_track_spotify' in track and track['key_track_spotify']]
        
        if not track_ids:
            return {"error": "No valid track IDs found in the provided tracks"}

        response = add_tracks_to_spotify_playlist(new_playlist['id'], track_ids)
       
        if isinstance(response, dict) and 'error' in response:
            return {'error': response['error']}
    except KeyError as e:
        return {"error": f"Missing expected key in track data: {str(e)}"}
    except TypeError as e:
        return {"error": f"Type error encountered: {str(e)}"}
    except Exception as e:
        return {"error": f"Error adding tracks to playlist: {str(e)}"}

    return {"playlist_id":playlist_id,"spotify_playlist_id": new_playlist['id'],"message": f"Spotify playlist \"{playlist_name}\" created successfully with {len(track_ids)} tracks"}






def get_set_searches(featured=None, sort_by="nb_results", page=1, per_page=200):
    
    # Start with the base query
    query = db.session.query(SetSearch)
    
    # Add a filter if 'featured' is not None
    if featured is not None:
        query = query.filter(SetSearch.featured == featured)
    
    # Apply ordering and pagination
    results = query.order_by(getattr(SetSearch, sort_by).desc()) \
                   .paginate(page=page, per_page=per_page, error_out=False)
    
    return results

    
    return results

def search_toggle_featured(set_search_id):
    set_search = db.session.query(SetSearch).get(set_search_id)
    if not set_search:
        return {"error": "Set search not found"}
    
    set_search.featured = not set_search.featured
    db.session.commit()
    
    return {"message": f"Set search featured status toggled to {set_search.featured}"}



def get_app_config_key(key):
    key = key.lower().strip()
    config = AppConfig.query.filter_by(key=key).first()
    if config:
        return config.value
    return None

def set_app_config_key(key, value):
    key = key.lower().strip()
    app_config = AppConfig.query.filter_by(key=key).first()
    if app_config:
        app_config.value = value
    else:
        app_config = AppConfig(key=key, value=value)
        db.session.add(app_config)
    db.session.commit()
    return app_config

def remove_app_config_key(key):
    key = key.upper().strip()
    app_config = AppConfig.query.filter_by(key=key).first()
    if app_config:
        db.session.delete(app_config)
        db.session.commit()
        return True
    return False


# Function to generate Apple Music Developer Token
def _generate_apple_music_dev_token():
    headers = {
        'alg': 'ES256',
        'kid': APPLE_KEY_ID
    }
    payload = {
        'iss': APPLE_TEAM_ID,
        'iat': int(time.time()),
        'exp': int(time.time()) + APPLE_TOKEN_EXPIRY_LENGTH,
        'aud': 'appstoreconnect-v1'
    }
    token = jwt.encode(payload, APPLE_PRIVATE_KEY, algorithm='ES256', headers=headers)
    set_app_config_key('apple_music_dev_token', token)
    set_app_config_key('apple_music_dev_token_expiry', int(time.time()) + APPLE_TOKEN_EXPIRY_LENGTH)
    return token

def get_apple_music_dev_token():
    # Get the current token
    token_value = get_app_config_key('apple_music_dev_token')
    if token_value:
        token_expiry = get_app_config_key('apple_music_dev_token_expiry')
        
        # Check if the token is expired
        if token_expiry and int(token_expiry) + APPLE_TOKEN_EXPIRY_LENGTH - 3600 < time.time():
            return token_value
   
    # token expired or not set, generate a new one
    new_token = _generate_apple_music_dev_token()
    return new_token



def get_user_extra_field(user, field):
    if not user.is_authenticated:
        
        return None 
   
    if user.extra_fields:
        return user.extra_fields.get(field, None)
    return None

def set_user_extra_field(user,field, value):
    
    if not user.is_authenticated:
        return False
    
    if not user.extra_fields or user.extra_fields is None:
        #user.extra_fields = {}  # Initialize as empty dictionary if None
        user.extra_fields = MutableDict()
    user.extra_fields[field] = value  # Set or update the field with the provided value
    
   
    try:
        
        db.session.commit()  # Commit the change to the database
        return True
    except Exception as e:
        db.session.rollback()
        #print(f'Error during commit: {e}')
        return False
  
   
   
def get_apple_music_user_token():
    token = get_user_extra_field(current_user, 'apple_music_user_token')
    if not token:
        return None
    return token


def set_apple_music_user_token(user,token):
    return set_user_extra_field(user, 'apple_music_user_token', token)

def remove_user_extra_field(user, field):
    if not user.is_authenticated:
        return None 
    
    if user.extra_fields and field in user.extra_fields:
        user.extra_fields.pop(field)  # Remove the field from the JSON
        db.session.commit()  # Commit the change to the database
        return True
    
    return False


def update_playlist_field(playlist,field,value):
    db.session.query(Playlist).filter_by(id=playlist['id']).update({field: value})
    db.session.commit()
    return True



def apple_playlist_exists(dev_token, user_token, playlist_id):
    url = f'https://api.music.apple.com/v1/me/library/playlists/{playlist_id}'

    headers = {
        'Authorization': f'Bearer {dev_token}',
        'Music-User-Token': user_token,
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)

    # Check if playlist exists
    if response.status_code == 200:
        playlist_data = response.json()

        # Check if 'data' is present and has at least one item
        if 'data' in playlist_data and len(playlist_data['data']) > 0:
            attributes = playlist_data['data'][0]['attributes']
            
            # Check if playlist has been deleted based on 'canEdit' and 'lastModifiedDate' values
            if attributes.get('canEdit') == False and attributes.get('lastModifiedDate') == '1970-01-01T00:00:00Z':
                
                return False
            else:
                
                return True
        else:
            
            return False

    # Handle 404 not found
    elif response.status_code == 404:
        
        return False

    # Handle other errors
    else:
        # print(f"Error: {response.status_code}")
        # print(response.text)
        return None


# Function to create a playlist for the user
def create_apple_playlist(dev_token, user_token, playlist_name, playlist_description=""):
    

    url = 'https://api.music.apple.com/v1/me/library/playlists'
    playlist_data = {
        "attributes": {
            "name": playlist_name,
            "description": playlist_description,
        }
    }

    headers = {
        'Authorization': f'Bearer {dev_token}',
        'Music-User-Token': user_token,
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=json.dumps(playlist_data))
    
    if response.status_code == 201:
        
        playlist = response.json()
        playlist_data = playlist['data'][0]
        return playlist_data  # Playlist details
    else:
        # print(f"Error: {response.status_code}")
        # print(response.text)
        return None
    
    
def get_track_ids_from_apple_playlist(dev_token,user_token,playlist_id):
    
    url = f'https://api.music.apple.com/v1/me/library/playlists/{playlist_id}/tracks'
    headers = {
        'Authorization': f'Bearer {dev_token}',
        'Music-User-Token': user_token,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            tracks_data = response.json()

            try:
                track_ids = [track['attributes']['playParams']['catalogId'] for track in tracks_data['data']]
            except Exception as e:
                logger.error(f"Error extracting track IDs: {str(e)}")
                track_ids = []

            
        else:
            # print(f"Error: {response.status_code} (in get_track_ids_from_apple_playlist)")
            # print(response.text)
            track_ids = []
        
    except Exception as e:
        return(f"Error: {str(e)} (in get_track_ids_from_apple_playlist)")
        
    return track_ids

def add_tracks_to_apple_playlist(dev_token,user_token,playlist_id, track_ids):
    """
    Adds tracks to a specified Apple Music playlist.

    Parameters:
    - dev_token: str, Developer Token for Apple Music API.
    - user_token: str, User Token obtained from MusicKit JS or similar.
    - playlist_id: str, The ID of the playlist to which tracks should be added.
    - track_ids: list of str, A list of track IDs to be added to the playlist.

    Returns:
    - response: dict, Response from the Apple Music API.
    """
    # Apple Music API endpoint for adding tracks to a playlist
    url = f'https://api.music.apple.com/v1/me/library/playlists/{playlist_id}/tracks'
    
    # Create the data payload for the request
    track_data = {
        "data": [{"id": track_id, "type": "songs"} for track_id in track_ids]
    }
    

    
    # Headers for the API request
    headers = {
        'Authorization': f'Bearer {dev_token}',
        'Music-User-Token': user_token,
        'Content-Type': 'application/json'
    }
    
    # Make the POST request to add tracks to the playlist
    try:
        response = requests.post(url, headers=headers, data=json.dumps(track_data))
    except Exception as e:
        return {"error": f"Error adding tracks: {str(e)}"}
    
    
    
    # Check if the request was successful
    if response.status_code == 204:
        return {"message": f"{len(track_ids)} tracks added to playlist"}
    elif response.status_code == 404:
        return []
    else: 
        response_json = response.json()
        if 'errors' in response_json:
            error_details = response_json['errors'][0]
            return {"error": f'{error_details["title"]} - {error_details["detail"]}'}
        
        return {"error": response.text}
    
def create_apple_playlist_and_add_tracks(dev_token,user_token,playlist_name, tracks,playlist):
    
    
    # check if playlist exists
    
   
    if not playlist:
        return {"error": "Playlist not found"}
    
    # does this playlist belong to user ?
    if playlist.get('user_id') != current_user.id:
        return {"error": "Unauthorized access to this playlist"}
    
    track_ids = [track['key_track_apple'] for track in tracks if 'key_track_apple' in track and track['key_track_apple']]
    if not track_ids:
        return {"error": "No valid Apple track IDs found in the provided tracks"}
    
    is_new_playlist = False
    # does this playlist exist on apple ?
    if not playlist.get('playlist_id_apple'):
        is_new_playlist = True
        try:
            # Create the Spotify playlist
            new_playlist = create_apple_playlist(dev_token,user_token,playlist_name,'Created from Set2Tracks')
            
            if not new_playlist:
                return {"error": "Error creating playlist"}
        except Exception as e:
            return {"error": f"Error creating playlist: {str(e)}"}
        
        playlist_id_apple = new_playlist['id']
        existing_tracks_ids = []
    else:
        playlist_id_apple = playlist.get('playlist_id_apple')
        playlist_still_exists = apple_playlist_exists(dev_token,user_token,playlist_id_apple)
        if not playlist_still_exists:
            update_playlist_field(playlist, 'playlist_id_apple',None)
            playlist['playlist_id_apple'] = None # update the playlist object as well
            return create_apple_playlist_and_add_tracks(dev_token,user_token,playlist_name, tracks,playlist)
        
        existing_tracks_ids = get_track_ids_from_apple_playlist(dev_token,user_token,playlist_id_apple)        
    
    if len(existing_tracks_ids) > 0:
        track_ids_to_add = list(set(track_ids) - set(existing_tracks_ids))
    else:
        track_ids_to_add = track_ids
        

            
    if len(track_ids_to_add) == 0:
        return {"error": "No new tracks to add to the playlist"}
    
    update_playlist_field(playlist, 'playlist_id_apple',playlist_id_apple)
    try:

        response = add_tracks_to_apple_playlist(dev_token,user_token,playlist_id_apple, track_ids_to_add)

        
        
        if 'error' in response:
            return {'error': response['error'],'track_ids':track_ids}
    except KeyError as e:
        return {"error": f"Missing expected key in track data: {str(e)}"}
    except TypeError as e:
        return {"error": f"Type error encountered: {str(e)}"}
    except Exception as e:
        return {"error": f"Error adding tracks to playlist: {str(e)}"}

    if is_new_playlist:
        return {"playlist_id":playlist['id'],"apple_playlist_id": playlist_id_apple,"message": f"Apple playlist \"{playlist_name}\" created successfully with {len(track_ids_to_add)} tracks"}
    else:
        return {"playlist_id":playlist['id'],"apple_playlist_id": playlist_id_apple,"message": f"Apple playlist \"{playlist_name}\" updated successfully with {len(track_ids_to_add)} tracks"}



