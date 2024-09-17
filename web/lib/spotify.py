import json
import os
from platform import release
from re import S
import time
from venv import logger
from flask import jsonify, redirect, request, session, url_for
import requests
import spotipy
from spotipy import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials,SpotifyOAuth
from web.lib.utils import extract_full_date, extract_year, safe_get
from web.lib.log_config import setup_logging;setup_logging()
import logging
import dotenv,os
from pprint import pprint

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
dotenv.load_dotenv(dotenv_path)
logger = logging.getLogger('root')

SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI') #'http://localhost:50001/spotify_callback'
PROXY_URL = os.getenv('SHAZAM_PROXY_URL')

# Scope for the data you want to access and modify
SCOPE = 'user-library-read playlist-read-private playlist-modify-public playlist-modify-private'


proxies = {
    'http': PROXY_URL,
    'https': PROXY_URL
}

client_credentials_manager = SpotifyClientCredentials(client_id=os.getenv('SPOTIFY_CLIENT_ID'), client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'))
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager) 





def convert_audio_features(data):
    def convert_and_check(value, multiplier=100): # conver from 0 to 1 to 0 to 100
        return int(value * multiplier) if value is not None else None
    
    def convert_and_check_loudness(value): # convert from -60 to 0 to 0 to 100
        return int((value + 60) / 60 * 100)  if value is not None else None

    return {
        'album': data.get('album'),
        'key_track_spotify': data.get('key_track_spotify'),
        'key_artist_spotify': data.get('key_artist_spotify'),
        'preview_uri_spotify': data.get('preview_uri_spotify'),
        'cover_art_spotify': data.get('cover_art_spotify'),
        'release_date': extract_full_date(data.get('release_date')), # 'release_date' is a typo in the database, but it's too late to change it now
        'release_year': extract_year(data.get('release_date')), # 'release_date' is a typo in the database, but it's too late to change it now
        'artist_genres_spotify': data.get('artist_genres_spotify'),
        'artist_popularity_spotify': data.get('artist_popularity_spotify'),
        'acousticness': convert_and_check(data.get('acousticness')),
        'danceability': convert_and_check(data.get('danceability')),
        'duration_s': convert_and_check(data.get('duration_ms'),0.001),
        'energy': convert_and_check(data.get('energy')),
        'key': data.get('key'),
        'mode': data.get('mode'),
        'liveness': convert_and_check(data.get('liveness')),
        'loudness': convert_and_check_loudness(data.get('loudness')),
        'instrumentalness': convert_and_check(data.get('instrumentalness')),
        'speechiness': convert_and_check(data.get('speechiness')),
        'tempo': convert_and_check(data.get('tempo'),1),
        'time_signature': data.get('time_signature'),
        'valence': convert_and_check(data.get('valence'))
    }
    
    
def add_tracks_audio_features_spotify(tracks):
    
    track_ids = [track.get('key_track_spotify') for track in tracks if track.get('key_track_spotify')]
    track_ids = list(set(track_ids))

    logger.info(f'Adding Spotify audio features to track_ids : {len(track_ids)}')
    logger.info(track_ids)
    try:
        logger.info('Getting audio features from Spotify...')
        audio_features = sp.audio_features(track_ids)
        
       
    except SpotifyException as e:
        logger.error(f'Error adding spotify audio features : {e}')
        raise SpotifyException(f'Spotify exception{e}')
    
    audio_features_dict = {af['id']: af for af in audio_features if af}
        
    # Add relevant audio features to each track
    for track in tracks:
        track_id = track.get('key_track_spotify', None)
        if track_id is not None and track_id in audio_features_dict:
            af = audio_features_dict[track_id]
            
            track['danceability'] = af.get('danceability')
            track['energy'] = af.get('energy')
            track['key'] = af.get('key')
            track['loudness'] = af.get('loudness')
            track['mode'] = af.get('mode')
            track['speechiness'] = af.get('speechiness')
            track['acousticness'] = af.get('acousticness')
            track['instrumentalness'] = af.get('instrumentalness')
            track['liveness'] = af.get('liveness')
            track['valence'] = af.get('valence')
            track['tempo'] = af.get('tempo')
            track['duration_ms'] = af.get('duration_ms')
            track['time_signature'] = af.get('time_signature')
            
            track.update(convert_audio_features(track))
            

            
    return tracks


def add_tracks_and_artist_spotify(track_title, artist_name,write_to_file=False):

    # Initialize variables, avoid errors if later not found
    album = None
    release_date = None
    song_id = None
    preview_uri = None
    cover_art_spotify = None
    artist_id = None
    artist_genres = None
    acousticness = None
    danceability = None
    duration_ms = None
    energy = None
    key = None
    mode = None
    liveness = None
    loudness = None
    instrumentalness = None
    speechiness = None
    tempo = None
    time_signature = None
    valence = None
    
    song = {}
    audio_features = {}
    artist_info = {}
    song_id = None

    try:
        song_info = sp.search(q=f'track:{track_title}, {artist_name}', type='track', limit=1)
        if song_info['tracks']['total'] > 0:        
            song = song_info['tracks']['items'][0]        
            song_id = song['id']
            logging.info(f'Song found by Spotify : "{track_title}", id: {song_id}')
        else:
            logging.info(f'Song not found by Spotify : "{track_title}"')
            
        
    except SpotifyException as e:
        logging.error(f'Error finding Spotify song : "{track_title}": {e}')

    except Exception as e:
        logging.error(f'Unknown error finding Spotify song : "{track_title}": {e}')
        logging.error(song_info)
        


    try:
        artist_info = sp.search(q=f'artist_name:{artist_name}', type='artist', limit=1)
        artist_fields = artist_info['artists']['items'][0]
        artist_id = artist_fields['id']
        artist_genres = artist_fields['genres']
        artist_popularity = artist_fields['popularity'] 
    except SpotifyException as e:
        logging.error(f'{e}')
    except Exception as e:
        logging.error(f'Artist fields not found "{artist_name}": {e}')

    if song_id is not None:
        try:
            preview_uri = song.get('preview_url', None)
            cover_art_spotify = safe_get(song, ['album','images',0,'url']) 
            album = safe_get(song, ['album','name'])
            release_date = safe_get(song, ['album','release_date'])
            duration_ms = safe_get(song, ['duration_ms'])
            
            
            # audio_features = sp.audio_features(song_id)
            # af_dict = audio_features[0] if audio_features else None
            # if af_dict is not None:
            #   acousticness = safe_get(af_dict, ['acousticness'])
            #   danceability = safe_get(af_dict, ['danceability'])
            #   duration_ms = safe_get(af_dict, ['duration_ms'])
            #   energy = safe_get(af_dict, ['energy'])
            #   key = safe_get(af_dict, ['key'])
            #   mode = safe_get(af_dict, ['mode'])
            #   liveness = safe_get(af_dict, ['liveness'])
            #   loudness = safe_get(af_dict, ['loudness'])
            #   instrumentalness = safe_get(af_dict, ['instrumentalness'])
            #   speechiness = safe_get(af_dict, ['speechiness'])
            #   tempo = safe_get(af_dict, ['tempo'])
            #   time_signature = safe_get(af_dict, ['time_signature'])
            #   valence = safe_get(af_dict, ['valence'])
    
        except SpotifyException as e:
            logging.error(f'{e}')
        except Exception as e:
            logging.error(f'{e}')
            
    if write_to_file:
        json_data ={}
        json_data['song'] = song
        json_data['artist_info'] = artist_info
        json_data['audio_features'] = audio_features
    
        json.dump(json_data, open(f'z-{track_title}.json', 'w'), indent=4)         

    return {
        'key_track_spotify': song_id,
        'key_artist_spotify': artist_id,
        'preview_uri_spotify': preview_uri,
        'album': album,
        'cover_art_spotify': cover_art_spotify,
        'release_date': release_date,
        'artist_genres_spotify': artist_genres,
        'artist_popularity_spotify': artist_popularity,
       # 'acousticness': acousticness,
       # 'danceability': danceability,
        'duration_ms': duration_ms,
        # 'energy': energy,
        # 'key': key,
        # 'mode': mode,
        # 'liveness': liveness,
        # 'loudness': loudness,
        # 'instrumentalness': instrumentalness,
        # 'speechiness': speechiness,
        # 'tempo': tempo,
        # 'time_signature': time_signature,
        # 'valence': valence
    }
    

import concurrent.futures

def add_tracks_spotify_data_from_json(tracks_json,try_count=0,max_tries=3):
    
    json.dump(tracks_json, open('tracks.json', 'w'), indent=4)
    
    def first_match(tracks,title,artist):
        first_match = None
        for track in tracks:
            if track['title'] == title and track['artist_name'] == artist:
                first_match = track
                break
        return first_match
   
    tracks_unique = {}
    try:
        for track in tracks_json:
            if track and 'title' in track and 'artist_name' in track and track['title'] and track['artist_name']:
                key = track['title'] + track['artist_name']
                if key not in tracks_unique:
                    tracks_unique[key] = track
    except Exception as e:
        logger.error(f'Error creating unique tracks: {e}')
        
                
    logger.info(f'Adding Spotify data to {len(tracks_unique)} unique tracks. Vs {len(tracks_json)} tracks total.')

    
    def process_track(track):
        if track and 'title' in track and 'artist_name' in track:
 
            song_info = add_tracks_and_artist_spotify(track['title'], track['artist_name'])
            if song_info:
                track.update(song_info)
            else:
                logger.error(f'Error adding Spotify data to track: {track}')
                # @TODO : add error handling
        return track
    
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            processed_tracks = list(executor.map(process_track, tracks_unique.values()))
            

        try:
            for original_track in tracks_json:
                if original_track and 'title' in original_track and 'artist_name' in original_track and original_track['title'] and original_track['artist_name']:
                    key = original_track['title'] + original_track['artist_name']
                    if key in tracks_unique:
                        updated_info = first_match(processed_tracks,original_track['title'],original_track['artist_name'])
                        
                        if updated_info:
                            # keep the start_time and end_time
                            # Otherwise, repeated songs would get the same start_time and end_time
                            # Need this check because this also runs on the related tracks, which don't have start_time and end_time
                            if 'start_time' in original_track and 'end_time' in original_track:
                                start_time = original_track['start_time']
                                end_time = original_track['end_time']
                                
                            original_track.update(updated_info)
                            
                            if 'start_time' in original_track and 'end_time' in original_track:
                                original_track['start_time'] = start_time
                                original_track['end_time'] = end_time
        except Exception as e:
            logger.error(f'Error updating original tracks: {e}')
            
            
        logger.info('Spotify data added to tracks.')
        logger.info('Adding audio features...')
       
        tracks_json = add_tracks_audio_features_spotify(tracks_json)
        
        # Todo : order tracks by start_time
        
       
        
    except SpotifyException as e:
        logger.error(f'Error: {e}')
        if try_count < max_tries:
            try_count += 1
            logger.error(f'Try count: {try_count}')
            logger.info(f'Retrying in {2 ** try_count} seconds.')
            time.sleep(2 ** try_count)
            return add_tracks_spotify_data_from_json(tracks_json,try_count=try_count,max_tries=max_tries)
        else:
            logger.error(f'Error: {e}')
            logger.error(f'Failed to add Spotify data to tracks after {max_tries} tries.')
            raise e
    except Exception as e:
        logger.error(f'error: {e}')
       

    return tracks_json




def get_spotify_oauth():
    return SpotifyOAuth(client_id=os.getenv('SPOTIFY_CLIENT_ID'), 
                        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'), 
                        redirect_uri=SPOTIPY_REDIRECT_URI, 
                        scope=SCOPE)

def get_client_auth_url():
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return auth_url
  
def get_client_token():
    sp_oauth = get_spotify_oauth()
    code = request.args.get('code')
    if code:
        logger.info(f'Code: {code}')
        token_info = sp_oauth.get_access_token(code)
        session['token_info'] = token_info
        return token_info
    
    logger.info('No code found in request.')
    return None

def is_token_expired(token_info):
    sp_oauth = get_spotify_oauth()
    return sp_oauth.is_token_expired(token_info)

def refresh_token(token_info):
    sp_oauth = get_spotify_oauth()
    token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    session['token_info'] = token_info
    return token_info

def get_valid_token():
    token_info = session.get('token_info', None)
    if not token_info:
        return None
    if is_token_expired(token_info):
        token_info = refresh_token(token_info)
    return token_info

def get_client_playlists():
    token_info = get_valid_token()
    if not token_info:
        return get_client_auth_url()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    playlists = sp.current_user_playlists()
    return playlists

def ensure_valid_token():
    token_info = session.get('token_info')
    if not token_info:
        return None

    if is_token_expired(token_info):
        token_info = refresh_token(token_info)

    return token_info['access_token']




def create_spotify_playlist(playlist_name, playlist_description=''):
    
    token_info = session.get('token_info', None)
    if not token_info:
        return 0
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.me()['id']
    playlist = sp.user_playlist_create(user_id, playlist_name, description=playlist_description)

    return playlist

# def add_tracks_to_spotify_playlist(playlist_id, track_uris_list):
    
#     token_info = session.get('token_info', None)
#     if not token_info:
#         return jsonify({'error': 'No Spotify token information found in session'})
    
#     try:
#         sp = spotipy.Spotify(auth=token_info['access_token'])
#         user_id = sp.me()['id']
#         print(f"User ID: {user_id}")
#         print(f"Playlist ID: {playlist_id}")
#         print(f"Track URIs: {track_uris_list}")

#         response = sp.user_playlist_add_tracks(user_id, playlist_id, track_uris_list)
       
#         return jsonify(response)
#     except spotipy.exceptions.SpotifyException as e:
#         return jsonify({'error': f'Spotify API error :{e}'})
#     except Exception as e:
#         return jsonify({'error': f'Error adding tracks to playlist: {e}'})

def add_tracks_to_spotify_playlist(playlist_id, track_uris_list):
    token_info = session.get('token_info')
    if not token_info:
        return jsonify({'error': 'No Spotify token information found in session'}), 400

    try:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user_id = sp.me()['id']

        response = sp.user_playlist_add_tracks(user_id, playlist_id, track_uris_list)
        
      
       
        return jsonify({'message':f'{len(track_uris_list)} tracks added to spotify playlist'})

    except spotipy.exceptions.SpotifyException as e:
        return jsonify({'error': f'Spotify API error: {e}'}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Network error: {e}'}), 503

    except KeyError as e:
        return jsonify({'error': f'Missing key in response: {e}'}), 500

    except Exception as e:
        return jsonify({'error': f'Unexpected error: {e}'}), 500


def get_spotify_playlist_tracks_ids(playlist_id):
    token_info = session.get('token_info')
    if not token_info:
        return jsonify({'error': 'No Spotify token information found in session'}), 400

    try:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user = sp.me()
        playlist = sp.user_playlist(user,playlist_id, fields='id')
        print ('playlist')
        print(playlist)
        if 'id' not in playlist:
            return jsonify({'error': 'Playlist not found'}), 404
        
        #print(f"Playlist: {playlist}")  # Debugging line
        #return jsonify({'error': 'wtf'})
        results = sp.playlist_tracks(playlist_id, fields='items(track(id,))')
        #print(f"Results: {results}")  # Debugging line
        return [item["track"]["id"] for item in results["items"]]
        
        return jsonify(results), 200

    except spotipy.exceptions.SpotifyException as e:
        return jsonify({'error': f'Spotify API error: {e}'}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Network error: {e}'}), 503

    except KeyError as e:
        return jsonify({'error': f'Missing key in response: {e}'}), 500

    except Exception as e:
        return jsonify({'error': f'Unexpected error: {e}'}), 500