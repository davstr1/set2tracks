import logging
import time
from web.controller.set_queue import insert_set_from_queue
from web import create_app
from boilersaas.utils.db import db

def worker_set_queue():
    app = create_app()
    with app.app_context():
        logger = logging.getLogger('root')
        logger.info('Queue Worker started')  # Log that the worker has started
        once = True
        while once == True:
            result = insert_set_from_queue()
            #once = False
            
            if result is None:
                logger.info('No more sets in the queue. Worker is idling.')
                time.sleep(10)  # Sleep for a bit before checking the queue again
            elif result == "failed":
                logger.warning('Failed to process set. Worker will continue.')
                # Optionally, you could sleep here for a short time before retrying
                time.sleep(1)
            else:
                logger.info(f'Successfully processed set: {result.id}')
                # Optionally, sleep for a short duration to prevent tight looping
                time.sleep(1)

if __name__ == '__main__':
    worker_set_queue()

    
    