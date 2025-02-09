from unittest import result
from boilersaas.utils.db import db

import asyncio

from shazamio import Shazam
from web.controller import add_tracks_from_json
from web.lib.apple import  add_apple_track_data_from_json_async
from web.lib.shazam import shazam_add_tracks_label, shazam_related_tracks
from web.lib.spotify import  add_tracks_spotify_data_from_json_async

async def async_save_related_tracks(track):
    
    error_msg = False
    
    try:
        track_id_shazam = track.key_track_shazam
        shazam = Shazam()
        tracks = await shazam_related_tracks(track_id_shazam, limit=30, shazam=shazam)
        
        if tracks:                    
            tasks = [
                shazam_add_tracks_label(tracks,30, shazam=shazam),
                add_tracks_spotify_data_from_json_async(tracks),
                add_apple_track_data_from_json_async(tracks)
            ]
            results = await asyncio.gather(*tasks)
             
            results = results[0]
            
            add_tracks_from_json(results, related_track_id=track.id)
            message = f"Related tracks saved for track ID {track.id}"
            
        else:
            message = f"No related tracks found for this track"
            error_msg = True
               
        track.related_tracks_checked = True
        db.session.commit()    
        
        if error_msg:
            return {'error': message}
        
        return {'message': message}  
    
    except Exception as e:

        return({'error':f"Exception Error saving related tracks : {e}"})
    
    
def save_related_tracks(track):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.ensure_future(async_save_related_tracks(track))  # Run inside existing loop
        else:
            return loop.run_until_complete(async_save_related_tracks(track))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(async_save_related_tracks(track))
    finally:
        if not loop.is_running():
            loop.close()