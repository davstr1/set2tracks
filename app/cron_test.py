import asyncio

import logging
import pprint

import time


# from shazamio import Shazam
#from web.lib.process_shazam_json import transform_track_data


# from web.lib.format import prepare_track_for_insertion
# from web.lib.utils import as_dict
# from web.model import Track
# from web.lib.av_apis.apple import  add_apple_track_data_one
# from web.lib.av_apis.spotify import  async_add_track_spotify_info
# from web.lib.av_apis.shazam import shazam_search_track,  shazam_track_add_label
from web import create_app
from web.lib.track_prompt import add_tracks_from_title_artists
from boilersaas.utils.db import db
# from typing import Dict, Any, Optional



def worker_set_queue():
    app = create_app()
    with app.app_context():
        logger = logging.getLogger('root')
        logger.info('Queue Worker started')  # Log that the worker has started

        

            
            
            
        track_titles_artists = [
                'Never Too Much - Luther Vandross',
                "Bigger Than Prince - Hot Since 82 Remix - Green Velvet",
                "Okay - Shiba San",
            ]

        asyncio.run(add_tracks_from_title_artists(track_titles_artists,db))
        
        # total_time = time.time() - total_start
        # print(f"Total execution time: {total_time:.2f} seconds")


if __name__ == '__main__':#
    worker_set_queue()


    
    