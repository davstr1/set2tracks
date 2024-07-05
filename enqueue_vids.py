from venv import logger
from sqlalchemy import MetaData
from boilersaas.utils.db import db
from web import create_app
import csv
import logging
logger = logging.getLogger('root')

from web.controller import queue_set
from web.model import SetQueue

def enqueue_videos_from_csv(csv_file_path, user_id=None):
    app = create_app()
    with app.app_context():
        with open(csv_file_path, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                try:
                    video_id = row[0].strip()
                    result = queue_set(video_id, user_id)

                    if isinstance(result, dict) and 'error' in result:
                        logger.error(f"Error for video_id {video_id}: {result['error']}")
                    elif isinstance(result, SetQueue) and result.id:
                        logger.info(f"Successfully queued video_id {video_id} with queue id {result.id}")
                    else:
                        logger.error(f"Unexpected result for video_id {video_id}: {result}")
                        
                except Exception as e:
                    logger.error(f"Error for video_id {video_id}: {e}")

# Example usage
enqueue_videos_from_csv('sets_to_enqueue.csv')