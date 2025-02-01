import asyncio
import json
import logging
import time
#from web.lib.process_shazam_json import transform_track_data
from web.lib.apple import  add_apple_track_data_from_json_async
from web.lib.spotify import  add_tracks_spotify_data_from_json_async
from web.lib.shazam import shazam_search_track, shazam_add_tracks_label
from web.lib.process_shazam_json import transform_track_data
from web import create_app
from boilersaas.utils.db import db
from typing import Dict, Any, Optional


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



def worker_set_queue():
    app = create_app()
    with app.app_context():
        logger = logging.getLogger('root')
        logger.info('Queue Worker started')  # Log that the worker has started

        async def main():
            semaphore = asyncio.Semaphore(50)  # Limit concurrent requests
            total_start = time.time()  # Start measuring total execution time

            start = time.time()
            track_info = await shazam_search_track("6 Underground – Sneaker Pimps", semaphore)
            print(track_info)
            if track_info is None:
                print("No track found")
                return
            print(f"Shazam search time: {time.time() - start:.2f} seconds")
            print('---------')

            start = time.time()
            track = transform_track_data(track_info)
            print(track)
            print(f"Transform track data time: {time.time() - start:.2f} seconds")
            print('---------')

            track_list = [track]
            
            # Execute these 3 functions in parallel
            start = time.time()
            results = await asyncio.gather(
                shazam_add_tracks_label(track_list),
                add_tracks_spotify_data_from_json_async(track_list),
                add_apple_track_data_from_json_async(track_list)
            )

            # Since `track` is the first return value of `asyncio.gather`, we assume
            # the functions are modifying the same track object in place (if not, adjust accordingly)
            print(results)
            
            print(f"Parallel execution time: {time.time() - start:.2f} seconds")
            print('---------')

            total_time = time.time() - total_start
            print(f"Total execution time: {total_time:.2f} seconds")

        asyncio.run(main())


if __name__ == '__main__':#
    worker_set_queue()


    
    