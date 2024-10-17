# def format_seconds(seconds:int)->str:
#     """Convert seconds to HH:MM:SS format."""
#     hours = seconds // 3600
#     minutes = (seconds % 3600) // 60
#     seconds = seconds % 60
#     return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

from calendar import c
import json
from math import e
from pprint import pprint
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from dateutil.relativedelta import relativedelta
from datetime import datetime, date

import pytz

from web.model import Genre, Track
import logging
logger = logging.getLogger('root')

def ensure_datetime_with_timezone(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = pytz.UTC.localize(value)
        return value
    elif isinstance(value, date):
        # Convert date to datetime (assuming midnight as time)
        value = datetime.combine(value, datetime.min.time())
        return pytz.UTC.localize(value)

def time_ago(value,less_than_a_day=True):
  
    now = datetime.now(pytz.UTC)  
    # If 'value' is naive, make it timezone-aware (assuming UTC or you can set your desired timezone)
    # if  value.tzinfo is None:
    #     value = pytz.UTC.localize(value)
    value = ensure_datetime_with_timezone(value)
    
    diff = relativedelta(now, value)
    
    if diff.years > 0:
        return f"{diff.years} year{'s' if diff.years > 1 else ''} ago"
    elif diff.months > 0:
        return f"{diff.months} month{'s' if diff.months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif not less_than_a_day:
        return 'today'
    elif diff.hours > 0:
        return f"{diff.hours} hour{'s' if diff.hours > 1 else ''} ago"
    elif diff.minutes > 0:
        return f"{diff.minutes} minute{'s' if diff.minutes > 1 else ''} ago"
    else:
        return "just now"
    
def km_number(value):
    if value is None:
        return '0'
    if value >= 1_000_000:
        formatted = value / 1_000_000
        return f"{formatted:.1f}m" if formatted % 1 != 0 else f"{int(formatted)}m"
    elif value >= 1_000:
        formatted = value / 1_000
        return f"{formatted:.1f}k" if formatted % 1 != 0 else f"{int(formatted)}k"
    else:
        return str(value)
    
def key_mode(track):
    key = track.get('key')
    mode = track.get('mode')
    if not key:
        return ''
    
    if mode == 1:
        return f'{key}B'

    return f'{key}A'
    

def spotify_track_url(track):
    # Extract title and subtitle from the dictionary
    track_id = track.get('key_track_spotify', '')
    if track_id:
        return f"spotify:track:{track_id}" 
    
    
    title = track.get('title', '')
    artist_name = track.get('artist_name', '')

    # Check if both title and subtitle are present
    if title and artist_name:
        search_query = f"{title} {artist_name}"
    else:
        search_query = title  # Assuming title is always present

    # Replace spaces with %20
    search_query = search_query.replace(" ", "%20")

    # Construct the Spotify search URL
    search_url = f"spotify:search:{search_query}"
    
    return search_url


def spotify_has_track(track):
    # Extract title and subtitle from the dictionary
    track_id = track.get('key_track_spotify', '')
    
    if track_id:
        return True
    return False

def apple_has_track(track):
    # Extract title and subtitle from the dictionary
    uri_apple = track.get('uri_apple', '')
    
    if uri_apple:
        return True
    return False


def apple_track_url(track):
    # Extract title and subtitle from the dictionary
    if track.get('id') == 1:
        return ''
    track_id = track.get('key_track_apple', '')
    track_uri = track.get('uri_apple', '')
    if track_uri:
        return track_uri
    
    if track_id:
        return f"https://itunes.apple.com/lookup?id={track_id}" 
    
    title = track.get('title', '')
    artist_name = track.get('artist_name', '')
    
    url = f"https://music.apple.com/us/search?term={title}+{artist_name}&entity=song"
    
    return url.replace(" ", "+")


def get_cover_art(track):
    
    # case in playlist page, or in general check if already parsed
    # track will then be a dict and already have the cover_art key
    if type(track) == dict:
        if 'cover_art' in track:
            return track['cover_art']
       
        
    no_cover_img = '/static/im/no_cover.png'
    unknown_track_cover = '/static/im/unknown_track_cover.png'
    
    try:
        track_id = track.id #track.get('id')
    except:
       return unknown_track_cover
    
    if track_id== 1:
        return unknown_track_cover
    
    
    cover_arts = track.cover_arts or {}
    cover_art_apple = cover_arts.get('apple')
    cover_art_spotify = cover_arts.get('spotify')
    if cover_art_apple:
        return cover_art_apple.replace("{w}", "400").replace("{h}", "400")
    
    if cover_art_spotify:
        return cover_art_spotify
    
    return no_cover_img
    

   
def get_preview_uri(track):
    track_preview_uris = track.preview_uris or {}
    return track_preview_uris.get('spotify') or track_preview_uris.get('apple') or '' # Apple are 30s, Spotify are 1m30s

def set_track_genres(track_json,db):
    """
    Set the genres for a track based on the given track JSON.

    Args:
        track_json (dict): The JSON object representing the track.

    Returns:
        list: A list of Genre objects for the track.
    """
    genres = set()

    # Get 'genre' value
    genre_name = track_json.get('genre', None)
    if genre_name:
        genres.add(genre_name.lower())

    # Get 'artist_genres' values
    artist_genres_spotify = track_json.get('artist_genres_spotify', None)
    if artist_genres_spotify:
         genres.update(genre.lower() for genre in artist_genres_spotify)
         
    genres_apple = track_json.get('genres_apple', None)
    if genres_apple:
         genres.update(genre.lower() for genre in genres_apple)

    # Convert the set to a list and handle case where genres are empty
    track_genre_names = [genre.replace('-', ' ') for genre in genres] if genres else ['none']

    # Convert genre names to Genre objects
    genre_objects = []
    for genre_name in track_genre_names:
        genre = Genre.query.filter_by(name=genre_name).first()
        if not genre:
            genre = Genre(name=genre_name)
            db.session.add(genre)
            db.session.flush()  # Ensure the genre is added to the session
        genre_objects.append(genre)

    return genre_objects


def format_db_track_for_template(track):

    try :     
        track_info = {
            'id': track.id, # how do i get the track id from the track_set ??
            'title': track.title,
            'artist_name': track.artist_name,
            'key_track_spotify': track.key_track_spotify,
            'key_track_shazam': track.key_track_shazam,
            'key_track_apple': track.key_track_apple,
            #'cover_arts': track.cover_arts,
            'cover_art': get_cover_art(track),
            'preview_uri': get_preview_uri(track),
            'uri_apple': track.uri_apple,
            'album': track.album,
            'label': track.label,
            'release_year': track.release_year,
            'artist_popularity_spotify': track.artist_popularity_spotify or 0,
           # 'start_time': track_set.start_time,
            #'end_time': track_set.end_time,
            'tempo': track.tempo,
            'key': track.key,
            'mode': track.mode,
            'danceability': track.danceability,
            'energy': track.energy,
            'valence': track.valence,
            'acousticness': track.acousticness,
            'instrumentalness': track.instrumentalness,
            'liveness': track.liveness,
            'loudness': track.loudness,
            'speechiness': track.speechiness,
            'time_signature': track.time_signature,
            'genres':track.genres,
            'has_related_tracks': track.has_related_tracks(),
            'nb_sets': track.nb_sets,
            #'pos': track_set.pos
            }
    except Exception as e:
        logging.error(f'Error in format_db_track_for_template : {e}')
        return {}
        
    return track_info

def format_db_tracks_for_template(tracks):
 
    tracks_info = []
    for track in tracks :

        track_info =format_db_track_for_template(track)
        tracks_info.append(track_info)
    
    return tracks_info

def format_tracks_with_times(tracks, track_set_dict):
    track_list = []
    
    i = 0
    for track in tracks:
        # start_time = track['start_time']
        # #track.end_time = track_set_dict[track_id]['end_time']
        # if 'start_time' in track_set_dict[start_time]:
        trackset_entry = track_set_dict[i]
       
        track['start_time'] = trackset_entry['start_time']
        track['end_time'] = trackset_entry['end_time']
            
        track['pos'] = trackset_entry['pos']
        track_list.append(track)
       
        i += 1
    

        
    return track_list

def format_tracks_with_pos(tracks, track_set_dict):
    track_list = []
    
    i = 0
    for track in tracks:
        # start_time = track['start_time']
        # #track.end_time = track_set_dict[track_id]['end_time']
        # if 'start_time' in track_set_dict[start_time]:
        trackset_entry = track_set_dict[i]
            
        track['pos'] = trackset_entry['pos']
        track_list.append(track)
       
        i += 1
    

        
    return track_list


def prepare_track_for_insertion(track_json,db):
    """
    Prepare a track object for insertion into the database.

    Args:
        track_json (dict): The JSON object representing the track.

    Returns:
        Track: The Track instance to be added to the database.
    """
    
    logger.debug('prepare_track_for_insertion')
    
    track = None
    
    key_track_shazam = track_json.get('key_track_shazam')
    key_track_shazam = int(key_track_shazam) if key_track_shazam not in [None, ""] else None

    key_track_spotify = track_json.get('key_track_spotify')
    key_track_spotify = key_track_spotify if key_track_spotify not in [None, ""] else None

    key_track_apple = track_json.get('key_track_apple')
    key_track_apple = key_track_apple if key_track_apple not in [None, ""] else None
    
    logger.debug(f'keys shape (shazam,spotify,apple): {key_track_shazam} {key_track_spotify} {key_track_apple}')
    
    
    if key_track_shazam is None and key_track_apple is None and key_track_spotify is None:
        track = Track.query.filter_by(id=1).first()
        logger.debug(f'No keys, using default unknown track')
        #db.session.add(track)
        return track
    
    # does this correspond to a track in the db ?
    # we have to check for the 3 keys
    
    if key_track_shazam is not None:
        track = Track.query.filter_by(key_track_shazam=key_track_shazam).first()
        if track:
            logger.debug(f'track with id {track.id} found with shazam key {key_track_shazam}')
            return track
        else:
            logger.debug(f'no track found in DB with shazam key {key_track_shazam}')
            
    if key_track_apple is not None:
        track = Track.query.filter_by(key_track_apple=key_track_apple).first()
        if track:
            logger.debug(f'track with id {track.id} found with apple key {key_track_apple}')
            return track
        else:
            logger.debug(f'no track found in DB with apple key {key_track_apple}')
    
    if key_track_spotify is not None:
        track = Track.query.filter_by(key_track_spotify=key_track_spotify).first()
        if track:
            logger.debug(f'track with id {track.id} found with spotify key {key_track_spotify}')
            return track
        else:
            logger.debug(f'no track found in DB with spotify key {key_track_spotify}')
            
    logger.debug('no track found in DB with any key. Let s create a new one')
  
    track = Track()
    db.session.add(track)
        
        
    # # Update track details
    track.key_track_spotify = track_json.get('key_track_spotify', None)
    track.key_track_apple = track_json.get('key_track_apple', None)
    track.key_track_shazam = track_json.get('key_track_shazam', None)
    track.key_artist_spotify = track_json.get('key_artist_spotify', None)
    track.key_artist_apple = track_json.get('key_artist_apple', None)
    track.key_track_apple = track_json.get('key_track_apple', None)
    track.title = cut_to_if_needed(track_json.get('title') or 'Track not found',255)
    track.artist_name = cut_to_if_needed(track_json.get('artist_name', None),255)
    track.cover_arts = {'apple':track_json.get('cover_art_apple', None), 'spotify':track_json.get('cover_art_spotify', None)}
    track.preview_uris = {'apple':track_json.get('preview_uri_apple', None), 'spotify':track_json.get('preview_uri_spotify', None)}
    track.uri_apple = track_json.get('uri_apple', None)
    track.album = track_json.get('album', None)
    track.label = track_json.get('label', None)
    # gave psycopg2.errors.InvalidTextRepresentation
    # "" stayed that way, erroring, with track_json.get('release_year', None)
    # apply solution here if reproducing : https://chatgpt.com/c/67113aa0-e35c-8002-8dd3-f3427be785c9
    track.release_year = track_json.get('release_year') or None 
    track.release_date = parse_date(track_json.get('release_date', None))
    track.genres = set_track_genres(track_json,db)
    track.artist_popularity_spotify = track_json.get('artist_popularity_spotify', 0)
    
    track.acousticness = track_json.get('acousticness', None)
    track.danceability = track_json.get('danceability', None)
    track.duration_s = track_json.get('duration_s', None)
    track.energy = track_json.get('energy', None)
    track.instrumentalness = track_json.get('instrumentalness', None)
    track.key = track_json.get('key', None)
    track.liveness = track_json.get('liveness', None)
    track.loudness = track_json.get('loudness', None)
    track.mode = track_json.get('mode', None)
    track.speechiness = track_json.get('speechiness', None)
    track.tempo = track_json.get('tempo', None)
    track.time_signature = track_json.get('time_signature', None)
    track.valence = track_json.get('valence', None)    
    return track   


def cut_to_if_needed(str,max_chars):
    if not str:
        return str
    if len(str) > max_chars:
        return str[:max_chars] 
    return str

def clean_apple_music_url(url):
    """
    Cleans an Apple Music URL by removing all query parameters except for the 'i' parameter.
    
    Args:
        url (str): The Apple Music URL to be cleaned.
        
    Returns:
        str: The cleaned Apple Music URL.
    """
    if url is None:
        return None
    
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Keep only the 'i' parameter
    filtered_params = {key: value for key, value in query_params.items() if key == 'i'}
    
    # Reconstruct the URL without other query parameters
    new_query_string = urlencode(filtered_params, doseq=True)
    new_url = urlunparse(parsed_url._replace(query=new_query_string))
    
    return new_url

def parse_date(date_str):
    if not date_str:  # Check for None, empty string, or other falsy values
        return None
    try:
        # Try to convert the date from 'DD-MM-YYYY' to 'YYYY-MM-DD' format
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        # If the date format is incorrect, return None or handle as needed
        return None
    
    
    
def format_set_queue_error(error, video_id = None):
    """
    Format an error message for the set queue.
    Args:
        error (str): The error message to be formatted.
    Returns:
        str: The formatted error message.
    """
    if not error:
        return ''
    if not video_id:
        return error

    # return all the text after video_id
    parts = error.split(video_id + ':')

    if len(parts) > 1:
        return parts[1].strip()
   
    return error
    