import asyncio
import json
import logging
import pprint
import re
import time

from requests import get
from shazamio import Shazam
#from web.lib.process_shazam_json import transform_track_data

from web.model import Track
from web.lib.av_apis.apple import  add_apple_track_data_from_json_async, add_apple_track_data_one
from web.lib.av_apis.spotify import  add_track_spotify_info, add_tracks_spotify_data_from_json_async, async_add_track_spotify_info
from web.lib.av_apis.shazam import shazam_search_track, shazam_add_tracks_label, shazam_track_add_label
from web import create_app
from boilersaas.utils.db import db
from typing import Dict, Any, Optional

def get_track_by_shazam_key(key_track_shazam):
    return Track.query.filter_by(key_track_shazam=key_track_shazam).first()   

def safe_get(d: Dict[str, Any], keys: list, default=None):
    """Safely retrieve nested dictionary values."""
    for key in keys:
        if isinstance(d, dict) and key in d:
            d = d[key]
        else:
            return default
    return d

def transform_track_data(response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Transforms track data from the provided response into a structured format."""
    
    # Extract track details safely
    hits = response.get("tracks", {}).get("hits", [])
    if not hits:
        print('no hits')
        return None  # No track found
    
    track = hits[0]  # First track found
    
    # Extract Apple Music store details safely
    apple_store = track.get("stores", {}).get("apple", {})
    preview_uri = apple_store.get("previewurl")
    cover_art = apple_store.get("coverarturl")
    key_track_apple = apple_store.get("trackid")
    
    return {
        "key_track_shazam": track.get("key"),
        "key_track_apple": key_track_apple,
        "title": safe_get(track, ["heading", "title"]),
        "artist_name": safe_get(track, ["heading", "subtitle"]),
        "cover_art_apple": cover_art,
        "preview_uri_apple": preview_uri,
        "genre": safe_get(track, ["genres", "primary"]),
        "subgenre": safe_get(track, ["genres", "subgenres"]),
        "album": safe_get(track, ["stores", "apple", "productid"]),  # Assuming productid maps to album
        "label": None,  # Not found in the provided data, adjust if necessary
        "release_year": None,  # Not found in the provided data, adjust if necessary
        "release_date": None  # Not found in the provided data, adjust if necessary
    }
    
async def process_single_track(track_title, semaphore, shazam):
    """ Fetch, transform, and process each track as soon as it's available. """
    track_info = await shazam_search_track(track_title, semaphore, shazam=shazam)
    if track_info is None:
        print(f"No track found for {track_title}")
        return None
    
    track = transform_track_data(track_info)
    
    
    track_already_there = get_track_by_shazam_key(track.get("key_track_shazam"))
    if track_already_there is not None :
        print(f"Track already exists: {track.get('title')} by {track.get('artist_name')}")
        
    else:   
        print(f"Processing track: {track.get('title')} by {track.get('artist_name')}")
    
        #track = [track] # next funcion is expecting a list of tracks
    
        # Process track data immediately
        await asyncio.gather(
            shazam_track_add_label(track, semaphore, shazam=shazam),  
            async_add_track_spotify_info(track), 
            add_apple_track_data_one(track) 
        )
        
    pprint.pprint(track)
    return track  # Optional: for debugging or logging



def worker_set_queue():
    app = create_app()
    with app.app_context():
        logger = logging.getLogger('root')
        logger.info('Queue Worker started')  # Log that the worker has started

        async def main():
            semaphore = asyncio.Semaphore(50)  # Limit concurrent requests
            total_start = time.time()  # Start measuring total execution time
            track_list = []
            start = time.time()
            shazam =Shazam()
            track_titles = [
                "Smells Like Teen Spirit",
                "Billie Jean",
                "Bohemian Rhapsody",
                "Shape of You",
                "Like a Rolling Stone",
                "Sweet Child O' Mine",
                "Hotel California",
                "Hey Jude",
                "Wonderwall",
                "Lose Yourself",
                "Cocaine",
                ]
            
            track_titles = [
                "Jack - Breach",
                "Bigger Than Prince - Hot Since 82 Remix - Green Velvet",
                "House Every Weekend - David Zowie",
                "Okay - Shiba San",
                "Stay (Don't Go) - Friend Within",
                "Shake & Pop - Green Velvet, Walter Phillips",
                "Renegade Master (Friend Within Remix) - Wildchild",
                "Detective - CamelPhat",
                "You Got The Love (Mark Knight Remix) - Candi Staton, The Source",
                "Under Control - Alesso, Calvin Harris, Hurts"
            ]
            
            track_titles = [
                'Never Too Much - Luther Vandross',
                "Bigger Than Prince - Hot Since 82 Remix - Green Velvet",
            ]
            
            tasks = [process_single_track(title, semaphore, shazam) for title in track_titles]
            processed_tracks = await asyncio.gather(*tasks)


            total_time = time.time() - total_start
            print(f"Total execution time: {total_time:.2f} seconds")

        asyncio.run(main())


if __name__ == '__main__':#
    worker_set_queue()


    
    