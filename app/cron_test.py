import asyncio
import logging
from web import create_app
from web.lib.track_prompt import add_tracks_from_title_artists
from boilersaas.utils.db import db


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


    
    