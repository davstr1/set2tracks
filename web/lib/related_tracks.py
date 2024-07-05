import json
from boilersaas.utils.db import db

import asyncio
from web.controller import add_tracks_from_json
from web.lib.apple import add_apple_track_data_from_json
from web.lib.shazam import shazam_related_tracks
from web.lib.spotify import add_tracks_spotify_data_from_json
from web.model import RelatedTracks

def save_related_tracks(track):
    
    try:
        track_id_shazam = track.key_track_shazam
        tracks = asyncio.run(shazam_related_tracks(track_id_shazam, limit=20))
        
        if tracks:                    
            tracks = add_tracks_spotify_data_from_json(tracks)
            
            tracks = add_apple_track_data_from_json(tracks)
         
            add_tracks_from_json(tracks, related_track_id=track.id)
            message = f"Related tracks saved for track ID {track.id}"
            
        else:
            message = f"No related tracks found for track ID {track.id}"
               
        track.related_tracks_checked = True
        db.session.commit()    
        return {'message': message}  
    
    except Exception as e:

        return({'error':f"Error saving related tracks: {e}"})
