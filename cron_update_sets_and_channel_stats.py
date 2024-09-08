import logging
import time
from web import create_app
from web.controller import  get_set_to_check, upsert_set
from web.lib.utils import as_dict, silent_function
from web.lib.youtube import youbube_video_info


def worker_set_queue():
    app = create_app()
    with app.app_context():
        logger = logging.getLogger('root')
        logger.info('Sets and channel Stats Worker started')  # Log that the worker has started
        once = True
        while once == True:
            set = get_set_to_check()
            set_info = as_dict(set)
            video_id = set.video_id
            title = set.title
            
            logger.info(f'Checking set {video_id} "({title})" ')

            video_info = youbube_video_info(video_id)
            logger.info(f'Got video info for {video_id}')

            
            upsert_set(video_info)
            #once = False
            
            #exit()
            time.sleep(1)

if __name__ == '__main__':
    worker_set_queue()

    
    