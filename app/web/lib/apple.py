import asyncio
import sys


import applemusicpy

from web.lib.utils import safe_get
import os
import dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
dotenv.load_dotenv(dotenv_path)
import logging
logger = logging.getLogger('root')


APPLE_KEY_ID = os.getenv('APPLE_KEY_ID')
APPLE_TEAM_ID = os.getenv('APPLE_TEAM_ID')
APPLE_PRIVATE_KEY = os.getenv('APPLE_PRIVATE_KEY').replace("\\n", "\n")
APPLE_TOKEN_EXPIRY_LENGTH = os.getenv('APPLE_TOKEN_EXPIRY_LENGTH')  # 6 months

#os.environ.pop("APPLE_PRIVATE_KEY", None)

if not all([APPLE_KEY_ID, APPLE_TEAM_ID, APPLE_PRIVATE_KEY]):
    logger.error("Error: One or more environment variables are not set.")
    sys.exit(1)


# logger.info(f'APPLE_KEY_ID: {APPLE_KEY_ID}')
# logger.info(f'APPLE_PRIVATE_KEY: {APPLE_PRIVATE_KEY}')
# logger.info('Apple API keys loaded from environment variables.')

# print(APPLE_PRIVATE_KEY)
# sys.exit(1)

def am_songs(song_ids_list: list) -> dict:
    def convert_and_check(value, multiplier=100): # conver from 0 to 1 to 0 to 100
        return int(value * multiplier) if value is not None else None

    

    keys = {
            'APPLE_KEY_ID': APPLE_KEY_ID,
            'APPLE_TEAM_ID': APPLE_TEAM_ID,
            'APPLE_PRIVATE_KEY': APPLE_PRIVATE_KEY
        }
    
        
    try:
       
        am = applemusicpy.AppleMusic(APPLE_PRIVATE_KEY, APPLE_KEY_ID, APPLE_TEAM_ID )
    except Exception as e:
        logger.error(f'error connecting to AppleMusic : {e}, {APPLE_KEY_ID}, {APPLE_TEAM_ID}, {APPLE_PRIVATE_KEY}')
        return {}
        
    
    try:
        

        results = am.songs(song_ids_list)
          
    except Exception as e:
        logger.error(f'error in am_songs: {e}')
        results = {}

    out = {}
    for item in results['data']:
        id_apple = safe_get(item, ['attributes','playParams', 'id'])
        genres =  safe_get(item, ['attributes','genreNames'])
        release_date = safe_get(item, ['attributes','releaseDate'])
        if release_date:
            release_year = release_date.split('-')[0]
        else:
            release_year = ''
        
        if len(genres) > 1:
            genres = [genre.lower() for genre in genres]
            genres = [genre for genre in genres if 'music' not in genre]
            

            
        inf = {
            'preview_uri_apple' : safe_get(item, ['attributes','previews', 0, 'url']),
            'cover_art_apple': safe_get(item, ['attributes','artwork', 'url']),
            'release_date' : release_date,
            'release_year' : release_year,
            'uri_apple': safe_get(item, ['attributes','url']),
            'genres_apple':  genres ,
            'key_artist_apple': safe_get(item, ['relationships','artists','data',0,'id']),
            'duration_s': convert_and_check(safe_get(item, ['attributes','durationInMillis']),0.001),
        }
        out[id_apple] = inf
        
    

    return out





def add_apple_track_data_from_json(tracks):
    key_apple_tracks = [song["key_track_apple"] for song in tracks]
    key_apple_tracks = list(set(filter(None, key_apple_tracks)))
   
    apple_tracks_info = am_songs(key_apple_tracks)
       
  
    for song in tracks:
        song.update(apple_tracks_info.get(song["key_track_apple"], {}))       
        
    return tracks

async def add_apple_track_data_from_json_async(tracks):
    """ Async wrapper for add_apple_track_data_from_json """
    return await asyncio.to_thread(add_apple_track_data_from_json, tracks)







    
    
    