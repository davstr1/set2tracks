import asyncio
from typing import Any, Dict, Optional

from shazamio import Shazam
from web.controller.track import get_track_by_shazam_key
from web.lib.av_apis.apple import add_apple_track_data_one
from web.lib.av_apis.shazam import shazam_search_track, shazam_track_add_label
from web.lib.av_apis.spotify import async_add_track_spotify_info
from web.lib.format import prepare_track_for_insertion
from web.lib.utils import as_dict, safe_get


def transform_track_data_from_shazam_search(response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
    
async def get_track_info_from_title_artist(track_title_artist, semaphore, shazam):
    """ Fetch, transform, and process one track from a title artist string. 
        Starts by shazam, then adds label, spotify and apple data, in parallel.
        If track already exists in db, it will not be processed again."""
    track_info = await shazam_search_track(track_title_artist, semaphore, shazam=shazam)
    if track_info is None:
        print(f"No track found for {track_title_artist}")
        return None
    
    track = transform_track_data_from_shazam_search(track_info)
    
    
    track_already_there = get_track_by_shazam_key(track.get("key_track_shazam"))
    if track_already_there is not None :
        print(f"Track already exists: {track.get('title')} by {track.get('artist_name')}")
        return as_dict(track_already_there)
    else:   
        print(f"Processing track: {track.get('title')} by {track.get('artist_name')}")
    
        #track = [track] # next funcion is expecting a list of tracks
    
        # Process track data immediately
        await asyncio.gather(
            shazam_track_add_label(track, semaphore, shazam=shazam),  
            async_add_track_spotify_info(track), 
            add_apple_track_data_one(track) 
        )
        
    return track  # Optional: for debugging or logging
  
  
async def add_tracks_from_title_artists(track_titles_artists: list,db):
          """Add tracks to the database from a list of title-artist strings.
          If the track is already in the database, it will not be added again"""
          semaphore = asyncio.Semaphore(50)  
          shazam =Shazam()
            
          tasks = [get_track_info_from_title_artist(title, semaphore, shazam) for title in track_titles_artists]
          processed_tracks = await asyncio.gather(*tasks)
          
          # insert tracks that aren't already in the database
          tracks_ret = []
          nb_tracks_inserted = 0
          for track in processed_tracks:
              if 'id' not in track:
                  nb_tracks_inserted += 1
                  tracks_ret.append (prepare_track_for_insertion(track, db))
              else:
                  tracks_ret.append(track)
                  
          
          db.session.commit()   
          
          # reparse tracks into dicts if they were inserted
          if nb_tracks_inserted > 0:
              tracks_ret = [as_dict(track) for track in tracks_ret] 
                  
          print(f'inerted: {nb_tracks_inserted} tracks')
          
          return tracks_ret

