from web.controller.set import extract_time_from_reason, is_set_exists, is_set_in_queue
from web.controller.set_process import insert_set, remove_set_temp_files
from web.lib.utils import as_dict
from web.lib.av_apis.youtube import youbube_video_info, youtube_video_exists
from web.model import  Set, SetQueue, Channel
from datetime import datetime, timedelta, timezone
from boilersaas.utils.db import db

from web.lib.format import cut_to_if_needed

from web.logger import logger

import dotenv

def clean_discarded_reason(reason, video_id=None):
    # Remove video_id from the reason. like in "n5l6paz89bg: this live event will begin in..."
    if video_id:
        reason = reason.replace(f"{video_id.lower()}:", "").strip()
        reason = reason.replace(f"[0;31mERROR:[0m [youtube] ", "").strip()
    reason = reason.lstrip(":").strip()
    return cut_to_if_needed(reason, 255)

def queue_set_discarded(video_id, reason, existing_entry=None):
    
    reason_cleaned = clean_discarded_reason(reason, video_id)
    
    if existing_entry:
        existing_entry.status = 'discarded'
        existing_entry.discarded_reason = reason_cleaned
        existing_entry.updated_at = datetime.now(timezone.utc)  # Manually update updated_at
        db.session.commit()
        return existing_entry
    
    discarded_entry = SetQueue(
        video_id=video_id,
        status='discarded',
        discarded_reason=reason_cleaned,
        updated_at=datetime.now(timezone.utc),  #
        n_attempts=1  
    )
    db.session.add(discarded_entry)
    db.session.commit()
    return {'error': reason_cleaned}
  

def queue_set_premiered(video_id, reason, existing_entry=None):
    # Extract time from the reason (only days, hours, or minutes, not a combination)
    premiere_duration = extract_time_from_reason(reason)
    premiere_ends = datetime.now(timezone.utc) + premiere_duration
    if 'live event' in reason:
        # Add 4 hours buffer to the live event time
         premiere_ends = premiere_ends + timedelta(hours=4)
         
    reason_cleaned = clean_discarded_reason(reason, video_id)
    
    if existing_entry:
        existing_entry.status = 'premiered'
        existing_entry.premiere_ends = premiere_ends
        existing_entry.discarded_reason = reason_cleaned
        existing_entry.updated_at = datetime.now(timezone.utc)  # Manually update updated_at
        db.session.commit()
        return existing_entry
    
    discarded_entry = SetQueue(
        video_id=video_id,
        status='premiered',
        premiere_ends=premiere_ends,
        discarded_reason=reason_cleaned,
        updated_at=datetime.now(timezone.utc),  #
        n_attempts=1  
    )
    db.session.add(discarded_entry)
    db.session.commit()
    return {'error': reason}

def queue_set_to_retry(video_id, reason, existing_entry=None):
    
    if existing_entry:
       return queue_reset_set(existing_entry,reason)
    
    failed_entry = SetQueue(
        video_id=video_id,
        status='prequeued',
        discarded_reason=reason,
        queued_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),  # Set updated_at for new entries
        n_attempts=1  # Initialize n_attempts for new entries
    )
    db.session.add(failed_entry)
    db.session.commit()
    #return failed_entry
    return {'error': reason}  
  
  
def queue_set(video_id,user_id=None,discard_if_exists=False,send_email=False,play_sound=False):
    # Queue a set for processing
    # update the channel sub count if it exists
    # we take advantage of the request to update the channel info
    
    if is_set_exists(video_id): # todo : the published stuff
        return {'error': 'Set was already here.','video_id':video_id}
    
    existing_queue_entry = is_set_in_queue(video_id)
    
    if existing_queue_entry:
        
        # user_id = existing_queue_entry.user_id
        # send_email = existing_queue_entry.send_email
        # play_sound = existing_queue_entry.play_sound
        
        if not discard_if_exists:
            if existing_queue_entry.status == 'discarded' or existing_queue_entry.status == 'failed':
                return {'error': f"Set was discarded from queue for the following reason: {existing_queue_entry.discarded_reason}. Please let us know if you think that's a mistake."}
 
        else:
            db.session.delete(existing_queue_entry)
            db.session.commit()
    
    if not youtube_video_exists(video_id):
        return queue_set_discarded(video_id,'Youtube Video doesn\t exist.',existing_queue_entry)
    
    try :
        video_info = youbube_video_info(video_id)
    except Exception as e:
        return queue_set_discarded(video_id,f'Error getting video info : "{str(e)}"',existing_queue_entry)
    
    if 'error' in video_info:
        video_info['error'] = video_info['error'].lower()
        if 'not a bot' in video_info['error'] or 'bot verification' in video_info['error']:
            return queue_set_to_retry(video_id, video_info['error'],existing_queue_entry)
        elif 'premiere' in video_info['error'] : #or 'this live event' in video_info['error']:
            return queue_set_premiered(video_id,video_info['error'],existing_queue_entry)
        
        return queue_set_discarded(video_id,video_info['error'],existing_queue_entry)
   
    if video_info is None:        
        return queue_set_discarded(video_id,'Error getting video info.',existing_queue_entry)
    
    chapters = video_info.get('chapters',[]) or []
    # ditch chapters if there are less than 5 songs.
    # We will then use the regular chapter less method
    # Reason : some sets are discarted, because the chapters are not done by songs
    # EX : mixtape : face A , face B
    if len(chapters) and len(chapters) < 5:
        chapters = []
        #return queue_set_discarded(video_id,f'{len(chapters)} songs in the chapters. Only sets with 5 or more songs are accepted.',existing_queue_entry)
    
    if video_info.get('duration',0) < 900:
        return queue_set_discarded(video_id,'Video shorter than 15m. Only sets longer than 15m are accepted.',existing_queue_entry)
    
    if video_info.get('duration',0) > 14400:
        return queue_set_discarded(video_id,'Video longer than 4h. Only sets shorter than 4h are accepted for now.',existing_queue_entry)

    
    if not video_info.get('playable_in_embed',False):
        return queue_set_discarded(video_id,'Video is not embeddable. (Set by the uploader)',existing_queue_entry)
    


    video_info_json = {
       'video_id': video_id, 
       'upload_date': video_info.get('upload_date'),
       'thumbnail': video_info.get('thumbnail'),
       'title': video_info.get('title'),
       'description': video_info.get('description'),
       'channel': video_info.get('channel'),
       'channel_id': video_info.get('channel_id'),
       'channel_url': video_info.get('channel_url'),
       'duration': video_info.get('duration'),
       'playable_in_embed': video_info.get('playable_in_embed'),
       'chapters': chapters,
       'channel_follower_count': video_info.get('channel_follower_count'),
       "like_count": video_info.get('like_count'),
        "view_count": video_info.get('view_count'),
       }
    
    # Extract the channel information
    channel_id = video_info.get('channel_id')
    channel_follower_count = video_info.get('channel_follower_count')

    # Check if the channel exists in the database
    channel = Channel.query.filter_by(channel_id=channel_id).first()

    if channel:
        # Log old and new follower count
        old_follower_count = channel.channel_follower_count
        new_follower_count = channel_follower_count

        if new_follower_count is not None and old_follower_count != new_follower_count:
            logger.info(f"Updating follower count for channel {channel_id}: {old_follower_count} -> {new_follower_count}")
            channel.channel_follower_count = new_follower_count
            channel.updated_at = datetime.now(timezone.utc)

        # Save the updated channel info to the database
        db.session.add(channel)

    # Commit the changes to the database
    db.session.commit()
    
    if existing_queue_entry:
        existing_queue_entry.status = 'pending'
        existing_queue_entry.discarded_reason = ''
        existing_queue_entry.queued_at = datetime.now(timezone.utc)
        existing_queue_entry.video_info_json = video_info_json
        existing_queue_entry.duration = video_info.get('duration', 0)
        existing_queue_entry.nb_chapters = len(chapters)
        # existing_queue_entry.send_email = send_email
        # existing_queue_entry.play_sound = play_sound
        db.session.commit()
        return existing_queue_entry
    
    
    queued_entry = SetQueue(
        video_id=video_id,
        user_id=user_id,
        status='pending',
        queued_at=datetime.now(timezone.utc),
        video_info_json=video_info_json,
        duration=video_info.get('duration', 0),
        nb_chapters=len(chapters),
        send_email=send_email,
        play_sound=play_sound
    )
    db.session.add(queued_entry)
    db.session.commit()
    return queued_entry
  
  
def queue_discard_set(set_queue_item):
    remove_set_temp_files(set_queue_item.video_id)
    set_queue_item.status = 'discarded'
    set_queue_item.updated_at = datetime.now(timezone.utc)
    set_queue_item.n_attempts += 1  
    db.session.commit()

def queue_reset_set(set_queue_item,discarded_reason=None):
    # Put the set back in the queue with the 'pending' status
    # If the set already has info, no need to make a whole queue set request
    if set_queue_item.video_info_json:
        set_queue_item.status = 'pending'
    else:
        set_queue_item.status = 'prequeued'
    
    set_queue_item.n_attempts += 1
    set_queue_item.updated_at=datetime.now(timezone.utc)
    set_queue_item.discarded_reason = discarded_reason
    db.session.commit()
    return set_queue_item
  
  
def pre_queue_set(video_id, user_id=None, discard_if_exists=False, send_email=False, play_sound=False):#
    """
    Pre-queue a set for processing.
    - If the set already exists, returns an error.
    - If 'discard_if_exists' is True, deletes existing queue entry before adding a new one.
    - Otherwise, it queues with status 'prequeued'.
    - Skips video info check for speed, as it's prone to bot verification and retries issues.
    """
    
    def to_bool(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('1', 'true', 'on', 'yes')
        return bool(value)

    send_email = to_bool(send_email)
    play_sound = to_bool(play_sound)
    
    
    if is_set_exists(video_id):
        return {'error': 'Set was already here.', 'video_id': video_id}
    
    existing_queue_entry = is_set_in_queue(video_id)
    
    if existing_queue_entry:
        if not discard_if_exists:
            existing_queue_entry = as_dict(existing_queue_entry)
            if existing_queue_entry['status'] in ['discarded', 'failed']:
                return {
                    'error': f"Set was discarded from queue for the following reason: {existing_queue_entry['discarded_reason']}. Please let us know if you think that's a mistake."
                }
            return {'error': 'Set already in queue.'}
        else:
            db.session.delete(existing_queue_entry)
            db.session.commit()

    if not youtube_video_exists(video_id):
        return queue_set_discarded(video_id, 'YouTube video does not exist.')

    # Create or update the queued entry
    queued_entry = SetQueue(
        video_id=video_id,
        user_id=user_id,
        status='prequeued',
        discarded_reason='',
        queued_at=datetime.now(timezone.utc),
        send_email=send_email,
        play_sound=play_sound
    )
    db.session.add(queued_entry)
    db.session.commit()
    
    return queued_entry


def insert_set_from_queue():
    
    logger.info('Starting insert_set_from_queue function')

    # Fetch the first pending entry queued_at ASC (FIFO)
    try:
        pending_entry = SetQueue.query.filter_by(status='pending').order_by(SetQueue.updated_at.asc()).first()
        #pending_entry = SetQueue.query.filter_by(id='23').first()
    except Exception as e:
        logger.error(f'Error fetching pending entry : {e}')
        # I had an error ERROR Error fetching pending entry : Can't reconnect until invalid transaction is rolled back.  Please rollback() fully before proceeding
        db.session.rollback() # Is this a real fix ? 
        return None
    
    if pending_entry is None:
        logger.info('No pending entry found')
        return None
    
    logger.debug(f'Fetched pending_entry: {pending_entry}')
    logger.debug(f'Pending entry ID: {pending_entry.id}')
    logger.debug(f'Pending entry video_id: {pending_entry.video_id}')


    if not pending_entry:
        logger.info('No pending entry found')
        return None
    

    # Update the status to 'processing' and commit
    pending_entry.status = 'processing'
    pending_entry.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    logger.info('Updated status to processing and committed changes')

    video_info = pending_entry.video_info_json
    result = insert_set(video_info)


    # Check result and update status accordingly
    
    # TODO : check for extra errors and implement premieres
    
    error_keywords = [
    'failed to extract any player response',
    'unable to download video',
    'not a bot',
    'bot verification',
    'InvalidTextRepresentation',
    'StringDataRightTruncation',
    'not available on this ap',
    'ffmpeg exited',
    '[0;31mERROR'
    ]
    
    premiere_keywords = [
       # 'live event will begin in ',
        'premieres in '
    ]

    if 'set_id' in result:
        pending_entry.status = 'done'
        logger.info('Set inserted successfully, updated status to done')
    else:
        distarted_reason = result.get('error', 'Unknown error')

        if any(keyword in distarted_reason for keyword in error_keywords):
            queue_reset_set(pending_entry,distarted_reason)
            
        # elif any(keyword in distarted_reason for keyword in premiere_keywords):
        #     pending_entry.status = 'premiered'
        #     # TODO: Implement premieres
        else:
            # Too long, too short, not enough tracks found errors
            
            pending_entry.status = 'discarded'
        
        logger.error(f'Set insertion {pending_entry.status}. Reason: {distarted_reason}')
        logger.error(result)
        pending_entry.n_attempts += 1
        pending_entry.discarded_reason = clean_discarded_reason(distarted_reason, pending_entry.video_id)
        

    # Commit the changes
    pending_entry.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    logger.info('Committed final changes')

    # Return the Set instance if successful, otherwise a string indicating failure
    if pending_entry.status == 'done':
        logger.info(f'Returning Set instance with id: {result["set_id"]}')
        return Set.query.get(result['set_id'])
    else:
        logger.info('Returning "failed" due to failure')
        return "failed"
      
      
def update_premiered_to_prequeued():
    # Get the current time
    now = datetime.now(timezone.utc)

    # Query to find rows with 'premiered' status and where premiere_ends < now
    items_to_update = db.session.query(SetQueue).filter(
        SetQueue.status == 'premiered',
        SetQueue.premiere_ends < now
    ).all()

    # Log how many elements were found
    count = len(items_to_update)
    logger.info(f"{count} items found to update from 'premiered' to 'prequeued'.")

    # Update each item if any are found
    if count > 0:
        for item in items_to_update:
            item.status = 'prequeued'
            item.updated_at = now

        # Commit the changes to the database
        db.session.commit()
