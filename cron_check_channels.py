from datetime import datetime, timezone
import logging
import time

from requests import get
import requests

from web import create_app
from web.controller import filter_out_existing_sets, get_channel_to_check, insert_set_from_queue, pre_queue_set, queue_set
from boilersaas.utils.db import db

from web.lib.youtube import youtube_get_channel_feed_video_ids
from web.model import SetQueue

def worker_set_queue():
    app = create_app()
    with app.app_context():
        logger = logging.getLogger('root')
        logger.info('Queue Worker started')  # Log that the worker has started
        once = True
        while once == True:
            channel = get_channel_to_check()
            channel_id = channel.channel_id
            logger.info(f'Checking channel {channel.author} ({channel_id}) for new sets')
            #videos_ids = youtube_get_channel_feed_video_ids(channel_id)
            try:
                videos_ids = youtube_get_channel_feed_video_ids(channel_id)
            except requests.exceptions.ConnectionError as e:
                logger.error(f'Connection error: {e}')
                time.sleep(5)  # Wait for 5 seconds before retrying
                continue  # Retry the loop
            
            logger.info(f'Found {len(videos_ids)} videos')
            videos_ids_new = filter_out_existing_sets(videos_ids)
            logger.info(f'Found {len(videos_ids_new)} new videos')
            
            if len(videos_ids_new) > 0:
                logger.info (f'Enqueuing first video in the list : {videos_ids_new[0]}')
                result = pre_queue_set(videos_ids_new[0]) #insert_set(video_id)
                
                if isinstance(result, dict) and 'error' in result:
                    logger.error(result['error'])
                    
                if isinstance(result, SetQueue) and result.id:
                    logger.info(f'Successfully enqueued set: {result.id}')
                
            channel.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            #once = False
            
            
            time.sleep(1)

if __name__ == '__main__':
    worker_set_queue()

    
    