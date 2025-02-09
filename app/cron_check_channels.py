from datetime import datetime, timezone
import logging
import time

from web.controller.channel import get_channel_to_check
from web.controller.set import filter_out_existing_sets
from web.controller.set_queue import pre_queue_set
from web import create_app
from boilersaas.utils.db import db

from web.lib.av_apis.youtube import youtube_get_channel_feed_video_ids
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
            except Exception as e:
                logger.error(f'Error occurred: {type(e).__name__}: {e}')
                time.sleep(5)  # Perform your action (e.g., sleep and retry)
                channel.updated_at = datetime.now(timezone.utc)
                db.session.commit()
                continue  # Retry the loop
            
            
            videos_ids_new = filter_out_existing_sets(videos_ids)
            logger.info(f'Found {len(videos_ids)} videos, {len(videos_ids_new)} new')
            
            
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

    
    