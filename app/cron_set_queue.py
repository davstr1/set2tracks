import logging
import time
from web.controller.set import get_first_prequeued_set
from web.controller.set_queue import queue_set, update_premiered_to_prequeued
from web import create_app
from web.lib.utils import as_dict

def worker_set_queue():
    app = create_app()
    with app.app_context():
        logger = logging.getLogger('root')
        logger.info('Queue Worker started')  # Log that the worker has started
        once = True
        while once == True:
            
            update_premiered_to_prequeued()
            
            prequeued = get_first_prequeued_set()
            
            #once = False
            
            if prequeued is None:
                logger.info('No more sets in the prequeue queue. Worker is idling.')
                time.sleep(10)  # Sleep for a bit before checking the queue again
            else:
                print('presueued:',as_dict(prequeued))
                queued_set = queue_set(prequeued.video_id)
                if isinstance(queued_set, dict) and 'error' in queued_set:
                    logger.error(f'Failed to process set with video_id {prequeued.video_id}. Worker will continue. Error: {queued_set["error"]}')
                    time.sleep(1)
                else:
                    logger.info(f'Successfully processed set: {queued_set.id}')
                    # Optionally, sleep for a short duration to prevent tight looping
                    time.sleep(1)
                
if __name__ == '__main__':
    worker_set_queue()

    
    