import json
import os
import re
import shutil
import time

from flask import url_for
from flask_login import current_user
import jwt
import requests
from sqlalchemy import  and_, func,  or_
from sqlalchemy.ext.mutable import MutableDict

from web.lib.apple import add_apple_track_data_from_json
from web.lib.audio import cut_audio
#from web.lib.insert_set import insert_set
from web.lib.count_unique_tracks import count_unique_tracks
from web.lib.process_shazam_json import write_deduplicated_segments, write_segments_from_chapter
from web.lib.shazam import sync_process_segments
from web.lib.spotify import add_tracks_spotify_data_from_json, add_tracks_to_spotify_playlist, create_spotify_playlist
from web.lib.utils import as_dict, calculate_avg_properties
from web.lib.youtube import download_youtube_video, youbube_video_info, youtube_video_exists
from web.model import AppConfig, Genre, Playlist, RelatedTracks, Set, SetBrowsingHistory, SetQueue, SetSearch, Track, TrackGenres, TrackPlaylist, TrackSet,Channel
from datetime import datetime, timedelta, timezone
from boilersaas.utils.db import db

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from collections import defaultdict
from web.lib.format import cut_to_if_needed, format_db_track_for_template, format_db_tracks_for_template, format_tracks_with_pos, format_tracks_with_times, prepare_track_for_insertion

from web.logger import logger

import dotenv

#from web.routes.routes_utils import is_admin
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
dotenv.load_dotenv(dotenv_path)

APPLE_KEY_ID = os.getenv('APPLE_KEY_ID')
APPLE_TEAM_ID = os.getenv('APPLE_TEAM_ID')
APPLE_PRIVATE_KEY = os.getenv('APPLE_PRIVATE_KEY').replace("\\n", "\n")
APPLE_TOKEN_EXPIRY_LENGTH = int(os.getenv('APPLE_TOKEN_EXPIRY_LENGTH'))  # 6 months
    
    
def get_track_by_shazam_key(key_track_shazam):
    return Track.query.filter_by(key_track_shazam=key_track_shazam).first()    
     

def get_track_by_id(id):
    return Track.query.filter_by(id=id).first()   

def get_tracks_min_maxes():
    # Get the minimum and maximum values for release year and BPM from every track in the database, excluding zeroes and nulls.
    year_min = Track.query.with_entities(func.min(Track.release_year)).filter(Track.release_year.isnot(None), Track.release_year != 0).scalar()
    year_max = Track.query.with_entities(func.max(Track.release_year)).filter(Track.release_year.isnot(None), Track.release_year != 0).scalar()
    bpm_min = Track.query.with_entities(func.min(Track.tempo)).filter(Track.tempo.isnot(None), Track.tempo != 0).scalar()
    bpm_max = Track.query.with_entities(func.max(Track.tempo)).filter(Track.tempo.isnot(None), Track.tempo != 0).scalar()
    instrumental_min = Track.query.with_entities(func.min(Track.instrumentalness)).filter(Track.instrumentalness.isnot(None), Track.instrumentalness != 0).scalar()
    instrumental_max = Track.query.with_entities(func.max(Track.instrumentalness)).filter(Track.instrumentalness.isnot(None), Track.instrumentalness != 0).scalar()
    acoustic_min = Track.query.with_entities(func.min(Track.acousticness)).filter(Track.acousticness.isnot(None), Track.acousticness != 0).scalar()
    acoustic_max = Track.query.with_entities(func.max(Track.acousticness)).filter(Track.acousticness.isnot(None), Track.acousticness != 0).scalar()
    speech_min = Track.query.with_entities(func.min(Track.speechiness)).filter(Track.speechiness.isnot(None), Track.speechiness != 0).scalar()
    speech_max = Track.query.with_entities(func.max(Track.speechiness)).filter(Track.speechiness.isnot(None), Track.speechiness != 0).scalar()
    danceability_min = Track.query.with_entities(func.min(Track.danceability)).filter(Track.danceability.isnot(None), Track.danceability != 0).scalar()
    danceability_max = Track.query.with_entities(func.max(Track.danceability)).filter(Track.danceability.isnot(None), Track.danceability != 0).scalar()
    energy_min = Track.query.with_entities(func.min(Track.energy)).filter(Track.energy.isnot(None), Track.energy != 0).scalar()
    energy_max = Track.query.with_entities(func.max(Track.energy)).filter(Track.energy.isnot(None), Track.energy != 0).scalar()
    loudness_min = Track.query.with_entities(func.min(Track.loudness)).filter(Track.loudness.isnot(None), Track.loudness != 0).scalar()
    loudness_max = Track.query.with_entities(func.max(Track.loudness)).filter(Track.loudness.isnot(None), Track.loudness != 0).scalar()
    valence_min = Track.query.with_entities(func.min(Track.valence)).filter(Track.valence.isnot(None), Track.valence != 0).scalar()
    valence_max = Track.query.with_entities(func.max(Track.valence)).filter(Track.valence.isnot(None), Track.valence != 0).scalar()
    return {
        'year_min': year_min, 'year_max': year_max, 
        'bpm_min': bpm_min, 'bpm_max': bpm_max, 
        'instrumental_min': instrumental_min, 'instrumental_max': instrumental_max,
        'acoustic_min': acoustic_min, 'acoustic_max': acoustic_max,
        'speech_min': speech_min, 'speech_max': speech_max,
        'danceability_min': danceability_min, 'danceability_max': danceability_max,
        'energy_min': energy_min, 'energy_max': energy_max,
        'loudness_min': loudness_min, 'loudness_max': loudness_max,
        'valence_min': valence_min, 'valence_max': valence_max
        }


def get_tracks(
        page=1,
        per_page=20,
        search=None,
        bpm_min=None,bpm_max=None,
        year_min=None,year_max=None,
        instrumental_min=None,instrumental_max=None,
        acoustic_min=None,acoustic_max=None,
        speech_min=None,speech_max=None,
        danceability_min=None,danceability_max=None,
        energy_min=None,energy_max=None,
        loudness_min=None,loudness_max=None,
        valence_min=None,valence_max=None,
        order_by=None,asc=None,
        genre=None,
        keys=''):
    
    query = Track.query
    
    if order_by == '':
        order_attr = Track.id
    else:
        order_attr = getattr(Track, order_by, None)
    
    if order_attr:
        query = query.filter(order_attr.isnot(None)) 
        if asc:
            query = query.order_by(order_attr.asc())
        else:
            query = query.order_by(order_attr.desc())
            
    if genre:
        query = query.join(Track.genres).filter(Genre.name.ilike(f"%{genre}%"))
        
    if search and search.strip():
        query = query.filter(
             or_(
            Track.title.ilike(f"%{search}%"),
            Track.artist_name.ilike(f"%{search}%"),
            Track.label.ilike(f"%{search}%"),
        )
        )
    
    if keys:
        # Parse the comma-separated string into individual keys
        parsed_keys = keys.split(",")  # Example: "A1,B2,A2" -> ["A1", "B2", "A2"]
        key_conditions = []
    
        for key in parsed_keys:
            mode = 0 if key[0] == 'A' else 1  # A = 0, B = 1
            key_number = int(key[1:])  # Extract the numeric value (e.g., "1" from "A1")
            
            # Create condition for exact match of key and mode
            key_conditions.append(and_(Track.mode == mode, Track.key == key_number))
    
        # Combine all conditions for an exact match
        query = query.filter(or_(*key_conditions))

        
    
    if bpm_min:
        query = query.filter(Track.tempo >= bpm_min)
    if bpm_max:
        query = query.filter(Track.tempo <= bpm_max)    
    if year_min:
        query = query.filter(Track.release_year >= year_min)
    if year_max:
        query = query.filter(Track.release_year <= year_max)
    if instrumental_min:
        query = query.filter(Track.instrumentalness >= instrumental_min)
    if instrumental_max:
        query = query.filter(Track.instrumentalness <= instrumental_max)
    if acoustic_min:
        query = query.filter(Track.acousticness >= acoustic_min)
    if acoustic_max:
        query = query.filter(Track.acousticness <= acoustic_max)
    if speech_min:
        query = query.filter(Track.speechiness >= speech_min)
    if speech_max:
        query = query.filter(Track.speechiness <= speech_max)
    if danceability_min:
        query = query.filter(Track.danceability >= danceability_min)
    if danceability_max:
        query = query.filter(Track.danceability <= danceability_max)
    if energy_min:
        query = query.filter(Track.energy >= energy_min)
    if energy_max:
        query = query.filter(Track.energy <= energy_max)
    if loudness_min:
        query = query.filter(Track.loudness >= loudness_min)
    if loudness_max:
        query = query.filter(Track.loudness <= loudness_max)
    if valence_min:
        query = query.filter(Track.valence >= valence_min)

        
    count = query.count()    
    
    # year_min = Track.query.with_entities(func.min(Track.release_year)).scalar()
    # year_max = Track.query.with_entities(func.max(Track.release_year)).scalar()
        
    ret = query.paginate(page=page, per_page=per_page, error_out=False)
    tracks_for_template  = format_db_tracks_for_template(ret.items)
    return tracks_for_template,ret,count

def get_or_create_channel(data):
    
    try:
        channel_id = str(data.get('channel_id'))
        existing_channel = Channel.query.filter_by(channel_id=channel_id).first()
        if existing_channel is not None:
            logger.info("Channel already exists.")
            return existing_channel
        
        logger.info("Creating new channel.")    
        new_channel = Channel(
            channel_id=channel_id,
            author=data.get('channel'),
            channel_url=data.get('channel_url'),
            channel_follower_count=data.get('channel_follower_count'),
            updated_at=datetime.now(timezone.utc)
        )
        db.session.add(new_channel)
        db.session.commit()
        return new_channel
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error in get_or_create_channel: {e}")
        return None

def validate_set_data(data):
    """ Validate set data to ensure it meets schema constraints. """
    required_fields = ['video_id', 'title', 'channel_id']
    for field in required_fields:
        if not data.get(field):
            logger.error(f"Missing required field: {field}")
            return False

    if 'duration' in data and not isinstance(data['duration'], int):
        logger.error(f"Invalid data type for duration: {type(data['duration'])}")
        return False

    if 'publish_date' in data:
        try:
            datetime.strptime(str(data['publish_date']), '%Y-%m-%d')
        except ValueError as e:
            logger.error(f"Invalid date format for publish_date: {data['publish_date']} : {str(e)}")
            return False

    return True

def get_set_id_by_video_id(video_id):
    set_record = Set.query.filter_by(video_id=video_id).first()
    return set_record.id if set_record else None


def get_set_queue_status(video_id):
    set_queue_record = SetQueue.query.filter_by(video_id=video_id).first()
    return set_queue_record.status if set_queue_record else None

def is_set_in_queue(video_id):
    # Check if the video is already in the queue
    existing_entry = SetQueue.query.filter_by(video_id=video_id).first()
    return existing_entry or False

def is_set_exists(video_id):
    # Check if the video is already in the queue
    existing_entry = Set.query.filter_by(video_id=video_id,published=True).first()
    return existing_entry is not None

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

def extract_time_from_reason(reason):
    # This function extracts time from the reason string
    # It searches for patterns like "in 2 days", "in 3 hours", or "in 5 minutes"
    
    # Check for "in a few" and treat it as 20 minutes
    # "the premiere will start in a few moments"
    if "in a few" in reason:
        return timedelta(minutes=20)
    
    days_match = re.search(r"(\d+)\s*day", reason)
    hours_match = re.search(r"(\d+)\s*hour", reason)
    minutes_match = re.search(r"(\d+)\s*minute", reason)

    if days_match:
        return timedelta(days=int(days_match.group(1)))
    elif hours_match:
        return timedelta(hours=int(hours_match.group(1)))
    elif minutes_match:
        return timedelta(minutes=int(minutes_match.group(1)))
    else:
        return timedelta()  # Default to no additional time if no match found

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



def is_set_exists_or_in_queue(video_id):   
    return is_set_exists(video_id) or is_set_in_queue(video_id)

def get_set_status(youtube_video_id:str) -> dict:
    """
    Get the status of a set based on the provided video_id.

    Args:
        youtube_video_id (str): The ID of the video.

    Returns:
        dict: A dictionary containing the status of the set. If the set exists, the status is returned. If the set is in the queue, the status of the queue entry is returned. If the set is not found, 'not_found' is returned.
    """
    existing_set = Set.query.filter_by(video_id=youtube_video_id).first()
    if existing_set and existing_set.published:
        return {'status': 'published'}
    
    existing_queue_entry = is_set_in_queue(youtube_video_id)
    if existing_queue_entry:
        return {'status': existing_queue_entry.status,'discarded_reason':existing_queue_entry.discarded_reason}
    return {'status': 'not_found'}

def filter_out_existing_sets(video_ids):
    """
    Filters out video IDs that already exist in the queue or in the database.

    Args:
        video_ids (list): A list of video IDs to check.

    Returns:
        list: A list of video IDs that are neither in the queue nor in the database.
    """
    return [video_id for video_id in video_ids if not is_set_exists_or_in_queue(video_id)]


def get_first_prequeued_set():
    return SetQueue.query.filter_by(status='prequeued').order_by(SetQueue.updated_at.asc()).first()


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
    if len(chapters) and len(chapters) < 5:
        return queue_set_discarded(video_id,f'{len(chapters)} songs in the chapters. Only sets with 5 or more songs are accepted.',existing_queue_entry)
    
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
       'chapters': video_info.get('chapters'),
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



def pre_queue_set(video_id, user_id=None, discard_if_exists=False, send_email=False, play_sound=False):
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



def upsert_set(data):
    
    try:
        # Ensure the channel exists
        channel = get_or_create_channel(data)
        if channel is None:
            logger.error("Channel could not be created or retrieved.")
            return None

        logger.info("Channel retrieved/created successfully.")

       

        # Query using video_id to ensure uniqueness
        existing_set = Set.query.filter_by(video_id=data['video_id']).first()
        
        publish_date = None
        if data.get('upload_date'):
            try:
                publish_date = datetime.strptime(data['upload_date'], '%Y%m%d').date()
                logger.info(f"Parsed publish_date: {publish_date}")
            except ValueError as ve:
                logger.error(f"Invalid upload_date format: {data['upload_date']}")
                return None

        try:
            
            
            
            if 'error' in data:
                # Upsert the error for the video_id
                logger.info("Error found. Upserting error for the video_id.")
                if existing_set:
                    existing_set.error = data['error']
                    existing_set.channel_id=channel.id
                    existing_set.updated_at = datetime.now(timezone.utc)
                   # existing_set.playable_in_embed = False
                else:
                    new_set = Set(
                        video_id=data['video_id'],
                        channel_id=channel.id,
                       # playable_in_embed=False,
                        error=data['error']
                    )
            else:
                
                  # Validate set data
                if not validate_set_data(data):
                    logger.error("Set data validation failed.")
                    return None
                
                # update everything about the channel. all this can change
                channel.channel_follower_count = data.get('channel_follower_count') or 0
                channel.author = data.get('channel')
                channel.channel_id = data.get('channel_id')
                channel.channel_url = data.get('channel_url')
                
                if existing_set:
                    logger.info("Set already exists. Updating existing set.")
                    existing_set.channel_id = channel.id
                    existing_set.title = data['title']
                    existing_set.duration = data.get('duration')
                    existing_set.publish_date = publish_date
                    existing_set.thumbnail = data.get('thumbnail')
                    existing_set.playable_in_embed = data.get('playable_in_embed', False)
                    existing_set.chapters = data.get('chapters')
                    existing_set.like_count = data.get('like_count') or 0
                    existing_set.view_count = data.get('view_count') or 0
                    existing_set.updated_at = datetime.now(timezone.utc) # needed if nothing else has changed
                    existing_set.error = '' # remove the error if it was there
                else:
                    logger.info("Creating new set.")
                    new_set = Set(
                        video_id=data['video_id'],
                        channel_id=channel.id,
                        title=data['title'],
                        duration=data.get('duration'),
                        publish_date=publish_date,
                        thumbnail=data.get('thumbnail'),
                        playable_in_embed=data.get('playable_in_embed', False),
                        chapters=data.get('chapters'),
                        like_count=data.get('like_count') or 0,
                        view_count=data.get('view_count') or 0
                    )

                    logger.info("New set instance created.")
                    db.session.add(new_set)
                    logger.info("New set added to session.")

            channel.nb_sets = db.session.query(Set).filter_by(channel_id=channel.id).filter(Set.error.is_(None), Set.playable_in_embed.is_(True)).count()

            db.session.commit()
            logger.info("Changes committed to database.")
            return existing_set or new_set
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError during set upsert: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return None
        except Exception as e:
            logger.error(f"Unexpected error during set upsert: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return None

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error in upsert_set: {e}")
        import traceback
        traceback.print_exc()
        return None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in upsert_set: {e}")
        import traceback
        traceback.print_exc()
        return None


    

def sanitize_query(query):
    # Trim whitespace, remove any non-alphanumeric characters (excluding spaces), and convert to lowercase
    sanitized_query = re.sub(r'[^a-zA-Z0-9 &]+', '', query).strip().lower()
    return sanitized_query

def upsert_setsearch(query, nb_results):
    sanitized_query = sanitize_query(query)
    
    # Check if the entry already exists
    existing_entry = db.session.query(SetSearch).filter(SetSearch.query == sanitized_query).first()
    
    if existing_entry:
        # Update the existing entry
        existing_entry.nb_results = nb_results
       # existing_entry.featured = featured
        existing_entry.updated_at = datetime.now(timezone.utc)
    else:
        # Create a new entry
        new_entry = SetSearch(
            query=sanitized_query,
            nb_results=nb_results,
            #featured=featured,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.session.add(new_entry)
    
    # Commit the transaction
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        raise
    
def get_sets_with_zero_track(page=1):
    query = Set.query.outerjoin(SetQueue, Set.video_id == SetQueue.video_id)
    query = query.filter(Set.nb_tracks==0)
    query = query.filter(SetQueue.id.isnot(None)) 
    query = query.with_entities(
    Set.id.label('set_id'),  
    SetQueue.id,
    SetQueue.video_id,                # Standard field names from SetQueue model
    SetQueue.user_id,
    SetQueue.user_premium,
    SetQueue.status,
    SetQueue.queued_at,
    SetQueue.updated_at,
    SetQueue.n_attempts,
    SetQueue.discarded_reason,
    SetQueue.video_info_json,
    SetQueue.duration,
    SetQueue.nb_chapters
)
    query = query.order_by(SetQueue.updated_at.desc())
    results_count = query.count()
    results = query.paginate(page=page, per_page=10, error_out=False)
    return results, results_count
    
def get_sets_in_queue(page=1, status=None,include_15min_error=True):
    #query = SetQueue.query
    query = SetQueue.query.outerjoin(Set, SetQueue.video_id == Set.video_id)
    query = query.with_entities(
    Set.id.label('set_id'),  
    SetQueue.id,
    SetQueue.video_id,                # Standard field names from SetQueue model
    SetQueue.user_id,
    SetQueue.user_premium,
    SetQueue.status,
    SetQueue.queued_at,
    SetQueue.updated_at,
    SetQueue.n_attempts,
    SetQueue.discarded_reason,
    SetQueue.video_info_json,
    SetQueue.duration,
    SetQueue.nb_chapters
)

    # Filter by status if provided
    if status:
        query = query.filter(SetQueue.status == status)
    else:
        # Default filter when no specific status is provided
        ##query = query.filter(SetQueue.status.in_(['pending', 'processing']))
        nothing = None
        
    if not include_15min_error:
        
        query = query.filter(
        or_(
        SetQueue.discarded_reason == None,           # Handle NULL values
        SetQueue.discarded_reason == '',             # Handle empty strings
        ~SetQueue.discarded_reason.like('%Video shorter than 15m%')   # Exclude '15min'
        )
    )

       #~SetQueue.discarded_reason.like('%Video shorter than 15m%') | (SetQueue.discarded_reason == None)

    # Get the total count before pagination
    total_count = query.count()

    # Order by SetQueue.id ascending
    query = query.order_by(SetQueue.updated_at.desc())

    # Paginate the results
    sets_per_page = 10  # Adjust this number based on how many sets you want per page
    paginated_sets = query.paginate(page=page, per_page=sets_per_page, error_out=False)

    # Return the paginated items and the total count as a tuple
    return paginated_sets, total_count


def upsert_set_browsing_history(set_id, user_id):
    # Check if the record exists
    history_item = SetBrowsingHistory.query.filter_by(set_id=set_id, user_id=user_id).first()
    
    if history_item:
        # Record exists, update the datetime (this happens automatically due to `onupdate=db.func.now()`)
        db.session.commit()
    else:
        # Record does not exist, insert new record
        new_history_item = SetBrowsingHistory(set_id=set_id, user_id=user_id)
        db.session.add(new_history_item)
        db.session.commit()

    return True


def count_sets_with_status(status, include_15min_error=True):
    query = SetQueue.query.filter_by(status=status)
    
    if not include_15min_error and status == 'discarded': # quick n dirty fix, was giving me extravagant results on "done" sets
        query = query.filter(
        ~SetQueue.discarded_reason.like('%Video shorter than 15m%')   # Exclude '15min'
        )
    return query.count()

def count_sets_with_all_statuses(include_15min_error=True):
    #distinct_statuses = SetQueue.query.with_entities(SetQueue.status).distinct().all()
    distinct_statuses = [status for status in SetQueue.__table__.columns['status'].type.enums]

    result = {}
    for status in distinct_statuses:
        result[status] = count_sets_with_status(status,include_15min_error) or 0
    # Not a proper status, but used to count sets with no tracks
    result['all'] = sum(result.values())
    result['zero_track'] = Set.query.filter_by(nb_tracks=0).count() or 0
    
    return result
    

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
    
    #return queue_set(set_queue_item.video_id, user_id=set_queue_item.user_id, discard_if_exists=True)


def get_my_sets_in_queue(user_id):
    return SetQueue.query.filter_by(user_id=user_id).order_by(SetQueue.id.desc()).limit(10).all()

def get_my_sets_in_queue_not_notified(user_id):
    # should retrieve only one a once, with the oldest first
    # first check if there is something errored
    set_in_queue = SetQueue.query.filter_by(user_id=user_id,play_sound=True,notification_sound_sent=False,status='failed').order_by(SetQueue.id.asc()).first()
    if not set_in_queue:
        set_in_queue = SetQueue.query.filter_by(user_id=user_id,play_sound=True,notification_sound_sent=False,status='discarded').order_by(SetQueue.id.asc()).first()
    if set_in_queue:
        return {'error': 'Something went wrong with a set you added :','set_queue_info':set_in_queue}   
    
    set_in_queue = SetQueue.query.filter_by(user_id=user_id,play_sound=True,notification_sound_sent=False,status='done').order_by(SetQueue.id.asc()).first()
    if set_in_queue:
        print('set_in_queue',set_in_queue)
        set_in_queue.notification_sound_sent = True
        db.session.commit()
        
        set_info  = Set.query.filter_by(video_id=set_in_queue.video_id).first()
        return {'message': f'Set {set_info.title} is ready. <a href="{url_for("set.set",set_id=set_info.id)}">Check it out</a>'}
    
    return None # no set to notify about
    
    
def get_channel_to_check():   
    channel = Channel.query.filter(Channel.channel_id != 'None',Channel.hidden == False,Channel.followable == True).order_by(Channel.updated_at.asc()).first() # yeah, mysterious channel with None id appears. @TODO

    return channel

# def get_set_to_check():   
#     set = Set.query.filter(((Set.error == '') | (Set.error == None)) & (Set.hidden == False)).order_by(Set.updated_at.asc()).first()
#    return set

def get_set_to_check():
    set_to_check = Set.query.join(Channel, Set.channel_id == Channel.id) \
        .filter(((Set.error == '') | (Set.error == None)) & (Set.hidden == False)) \
        .filter(Channel.channel_id != 'None', Channel.hidden == False, Channel.followable == True) \
        .order_by(Set.updated_at.asc()) \
        .first()
    
    return set_to_check


def get_set_to_check_with_error():   
    set = Set.query.filter(Set.error != '').order_by(Set.updated_at.asc()).first()


    return set
        
    
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
    
    
    
    

AUDIO_SEGMENTS_LENGTH = int(os.getenv('AUDIO_SEGMENTS_LENGTH'))#

def error_out(msg):
    return({'error':msg})


def merge_tracks_by_shazam_key(tracks, look_ahead):
    """
    Merges track records based on their 'key_track_shazam' field, looking ahead within a specified range
    to find and merge duplicate records. The function updates track records by extending 'end_time' and
    filling in missing details from duplicate records found within the look-ahead range.

    Args:
        tracks (list of dict): List of track records, each with 'key_track_shazam' and other metadata.
        look_ahead (int): Number of subsequent records to check for duplicates based on 'key_track_shazam'.

    Returns:
        list of dict: List of merged and updated track records.
    """

    def update_record(current, new):
        """Update current record with non-empty values from new record, except 'start_time'."""
        for key, value in new.items():
            if key != 'start_time' and value and not current.get(key):
                current[key] = value

    processed_tracks = []
    i = 0

    while i < len(tracks):
        current_track = tracks[i]
        j = i + 1

        while j < len(tracks) and j <= i + look_ahead:
            if current_track['key_track_shazam'] is not None and tracks[j]['key_track_shazam'] == current_track['key_track_shazam']:
                current_track['end_time'] = tracks[j]['end_time']
                update_record(current_track, tracks[j])
                i = j  # move to the next record after the found duplicate
            j += 1

        processed_tracks.append(current_track)
        i += 1

    return processed_tracks

def remove_small_unidentified_segments(tracks, min_duration_s):
    """
    Removes small unidentified segments from a list of tracks and adjusts the end time of the previous identified track accordingly.

    Parameters:
    tracks (list of dict): A list of track dictionaries, where each dictionary represents a track with 'title', 'start_time', and 'end_time' keys.
    min_duration_s (int or float): The minimum duration in seconds. Unidentified tracks with a duration less than this value will be removed.

    Returns:
    list of dict: A cleaned list of tracks with small unidentified segments removed and the end times of the previous identified tracks adjusted.

    Example:
    tracks = [
        {'title': 'Song 1', 'start_time': 0, 'end_time': 30},
        {'title': '', 'start_time': 30, 'end_time': 32},  # This will be removed if min_duration_s is > 2
        {'title': 'Song 2', 'start_time': 32, 'end_time': 60}
    ]
    min_duration_s = 3
    cleaned_tracks = remove_small_unidentified_segments(tracks, min_duration_s)
    # cleaned_tracks will be:
    # [
    #     {'title': 'Song 1', 'start_time': 0, 'end_time': 32},
    #     {'title': 'Song 2', 'start_time': 32, 'end_time': 60}
    # ]
    """
    
    cleaned_tracks = []

    for i in range(len(tracks)):
        current_track = tracks[i]

        # If the current track is unidentified and its duration is less than min_duration_s
        if (not current_track['title']) and (current_track['end_time'] - current_track['start_time'] < min_duration_s):
            # Extend the end_time of the previous identified track if there is one
            if cleaned_tracks:
                cleaned_tracks[-1]['end_time'] = current_track['end_time']
        else:
            cleaned_tracks.append(current_track)

    return cleaned_tracks

dl_dir = 'temp_downloads'


def insert_set(video_info,delete_temp_files=True):
    try:
        
        
        video_id = video_info['video_id']
        chapters = video_info.get('chapters',[])
        if chapters is None:
            chapters = []
       

        set = upsert_set(video_info)  
        if set is None:
            return error_out("Error creating Set.")


        logger.info('Setup directories')
        vid_dir = f"{dl_dir}/{video_id}"
        segments_dir = f"{vid_dir}/segments"
        shazam_json_dir = f"{vid_dir}/shazam_json"  
        dedup_segments_filepath = f'{vid_dir}/segments_dedup.json'  
        complete_songs_path = f'{vid_dir}/songs_complete.json'
        full_opus_path = f'{vid_dir}/full.opus'
        os.makedirs(vid_dir,exist_ok=True)
        os.makedirs(segments_dir,exist_ok=True)
        os.makedirs(shazam_json_dir,exist_ok=True)
    
        logger.debug(f"Constructed path: '{full_opus_path}'")
        if not os.path.exists(full_opus_path):
            logger.info(f'Downloading video {video_id}')
            download_youtube_video(video_id,vid_dir)
        else:
            logger.info(f'Video {video_id} already downloaded.')
        
        if not os.path.exists(dedup_segments_filepath):
            cut_audio(full_opus_path,chapters, AUDIO_SEGMENTS_LENGTH, None, segments_dir)
            sync_process_segments(segments_dir, shazam_json_dir)
            if not len(chapters):
                write_deduplicated_segments(shazam_json_dir, dedup_segments_filepath,AUDIO_SEGMENTS_LENGTH)
            else:
                write_segments_from_chapter(shazam_json_dir, dedup_segments_filepath, chapters)

    
        if not os.path.exists(complete_songs_path) or True :
            songs = json.load(open(dedup_segments_filepath))
            
            songs = merge_tracks_by_shazam_key(songs, 4)
      
            
            songs = remove_small_unidentified_segments(songs, 90)
            #json.dump(songs,open('shazam_songs.json','w'),indent=4)
            nb_unique_tracks = count_unique_tracks(songs)
            logger.debug(f'Found {nb_unique_tracks} unique tracks.')
            if nb_unique_tracks < 5:
                raise Exception(f'{nb_unique_tracks} unique tracks found. Min 5')
            
            songs = add_tracks_spotify_data_from_json(songs)
           
            songs = add_apple_track_data_from_json(songs)
            
            json.dump(songs,open(complete_songs_path,'w'),indent=4)
            
        songs = json.load(open(complete_songs_path))
        
        add_tracks_from_json(songs,set,add_to_set=True)

        if delete_temp_files:
            shutil.rmtree(vid_dir)

        return {'set_id':set.id}
    except Exception as e:
        if delete_temp_files:
            shutil.rmtree(vid_dir)
        return error_out(str(e)) 
    
    
def remove_set_temp_files(video_id):
    vid_dir = f"{dl_dir}/{video_id}"
    if os.path.exists(vid_dir):
        shutil.rmtree(vid_dir)
        return True
    return False
    

def add_tracks_from_json(tracks_json, set_instance=None, add_to_set=False,related_track_id=None):
    """
    Adds tracks from a JSON object to the database.

    Args:
        tracks_json (list): A list of track objects in JSON format.
        set_instance (Set, optional): The set instance to which the tracks belong. Defaults to None.
        add_to_set (bool, optional): Indicates whether to add the tracks to the set. Defaults to False.

    Raises:
        ValueError: If add_to_set is True but set_instance is None.
        Exception: If an error occurs during the process.

    Returns:
        None
    """
    
    if add_to_set and set_instance is None:
        raise ValueError("set_instance cannot be None")
    
    if related_track_id and add_to_set:
        raise ValueError("related_track_id cannot be provided when add_to_set is True")
    
    db.session.autoflush = False
    pos = 0
    unique_tracks = set()  
    
    try:
        for track_json in tracks_json:
            
            try:
                track = prepare_track_for_insertion(track_json,db)
            except Exception as e:
                logger.error(f"Error preparing track for insertion: {e}")
                
            
    

            db.session.flush()  # Flush here to ensure 'track.id' is filled
            
            unique_tracks.add(track)

            start_time = track_json.get('start_time', 0)
            end_time = track_json.get('end_time',0)
            pos = pos + 1

            # Check if TrackSet already exists
            if add_to_set:
                track_set = TrackSet.query.filter_by(track_id=track.id, set_id=set_instance.id, pos=pos).first()
                if not track_set:
                    track_set = TrackSet(
                        track_id=track.id,
                        set_id=set_instance.id,
                        start_time=start_time,
                        end_time=end_time,
                        pos=pos
                    )

                    db.session.add(track_set)
                    logger.info(f"Added new TrackSet entry with track_id={track.id}")
                else:
                    logger.info("TrackSet entry already exists, skipping insertion.")

                    pos += 1  # Increment position regardless of addition
            
                set_instance.nb_tracks = len(unique_tracks)
                db.session.add(set_instance)
        
        # Update n_sets for all unique tracks
        for track in unique_tracks:
            if add_to_set:
                track.nb_sets = (track.nb_sets or 0) + 1
            db.session.add(track)
        
        # Add set info and publish set    
        if add_to_set:
            set_characteristics = calculate_avg_properties(tracks_json)
            for key, value in set_characteristics.items():
                setattr(set_instance, key, value)
                
            set_instance.published = True 
         
        
        db.session.commit()
        
        # Set related_tracks if related_track_id is provided
        if related_track_id and not add_to_set:
            logger.info(f'Related track ID provided: {related_track_id}')
            related_track_entries = []

           
        related_track = Track.query.filter_by(id=related_track_id).first()

        if related_track:
            logger.info('Related track found.') # goes here
            for i, track in enumerate(unique_tracks):
                track.insertion_order = i
                related_track_entries.append(RelatedTracks(track_id=related_track.id, related_track_id=track.id, insertion_order=i))

            # Add all the related track entries to the session
            for entry in related_track_entries:
                db.session.add(entry)
            
            db.session.commit() 
        
        
    except Exception as e:
        db.session.rollback()
        logger.info("An error occurred:", e)
        raise e
    finally:
        db.session.autoflush = True  # Ensure autoflush is enabled again
        
def compile_and_sort_genres(track_sets):
    genre_counts = defaultdict(int)

    for track_set, track in track_sets:
        for genre in track.genres:
            genre_counts[genre.name] += 1

    sorted_genre_counts = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_genre_counts


def get_playable_sets(page=1, per_page=20, search=None, order_by='latest_youtube'):
    
    prefixed_search = False
    
    if search and search.startswith('trackid:'):
        track_id = search[len('trackid:'):]
        #TODO check for numeric value
        # check for existence of track
        prefixed_search = True
        query = (
        Set.query.filter_by(playable_in_embed=True, published=True,hidden=False) \
        .join(TrackSet, Set.id == TrackSet.set_id)
        .join(Set.channel) \
        .filter(Set.channel.has(hidden=False)) \
        .options(joinedload(Set.channel))
        .filter(TrackSet.track_id == track_id)
        )
        
    elif search and search.startswith('channelid:'):
        channel_id = search[len('channelid:'):]
        # TODO check for numberic value
        # check for existence of channel
        prefixed_search = True
        query = Set.query.filter_by(playable_in_embed=True, published=True,hidden=False,channel_id=channel_id) 
        
        
    else: 
        query = Set.query.filter_by(playable_in_embed=True, published=True,hidden=False) \
                     .join(Set.channel) \
                     .filter(Set.channel.has(hidden=False)) \
                     .options(joinedload(Set.channel))
                     
    

    if search and not prefixed_search:
                 
          # Use SQLAlchemy's or_ to create an OR condition
        search_filter = or_(
              Set.title_tsv.match(search),  # Assuming title_tsv is a full-text search vector
              Channel.author.match(search)  # Assuming author is also a searchable field
          )
          
        query = query.filter(search_filter)

        # Print the generated SQL query for debugging
        # print(str(query.statement))


    
    if order_by == 'latest_youtube':
        query = query.order_by(Set.publish_date.desc())
    elif order_by == 'latest_set2tracks':
        query = query.order_by(Set.id.desc())
    elif order_by == 'channel_popularity':
        query = query.order_by(Channel.channel_follower_count.desc())
    
    # 
    # OBSOLETE for now
    #
    # elif order_by == 'old':
    #     query = query.order_by(Set.publish_date.asc())
    # elif order_by == 'likes':
    #     query = query.order_by(Set.like_count.desc())
    # elif order_by == 'views':
    #     query = query.order_by(Set.view_count.desc())
    # elif order_by == 'views_minus':
    #     query = query.order_by(Set.view_count.asc())
    # elif order_by == 'likes_minus':
    #     query = query.order_by(Set.like_count.asc())
    # elif order_by == 'small_channel':
    #     query = query.order_by(Channel.channel_follower_count.asc())

    
    results_count = query.count()
    results = query.paginate(page=page, per_page=per_page, error_out=False)
    if search and not prefixed_search:
        upsert_setsearch(search, results_count)
    return results,results_count


def get_browsing_history(user_id, page=1, per_page=20, order_by='recent', search=None):
    # Query to fetch the browsing history for the given user
    query = db.session.query(Set).join(SetBrowsingHistory, Set.id == SetBrowsingHistory.set_id) \
                .join(Channel, Set.channel_id == Channel.id) \
                .filter(SetBrowsingHistory.user_id == user_id) \
                .filter(Set.playable_in_embed == True, Set.published == True, Channel.hidden == False)
    # If there's a search term, apply it to filter the results based on the set's title or channel's author
    if search:
        search_filter = or_(
            Set.title_tsv.match(search),  # Assuming title_tsv is a full-text search vector for the set title
            Set.channel.has(Channel.author.ilike(f'%{search}%'))  # Assuming the author field is searchable
        )
        query = query.filter(search_filter)

    # Ordering based on the order_by parameter
    if order_by == 'recent':
        query = query.order_by(SetBrowsingHistory.datetime.desc())
    elif order_by == 'old':
        query = query.order_by(SetBrowsingHistory.datetime.asc())
    elif order_by == 'views':
        query = query.order_by(Set.view_count.desc())
    elif order_by == 'likes':
        query = query.order_by(Set.like_count.desc())
    
    # Get total results count
    results_count = query.count()

    # Paginate results
    results = query.paginate(page=page, per_page=per_page, error_out=False)

    return results, results_count


                    
def get_playable_sets_number():
    query = Set.query.filter_by(playable_in_embed=True, published=True,hidden=False) \
                     .join(Set.channel) \
                     .filter(Set.channel.has(hidden=False)) \
                     .options(joinedload(Set.channel))
    return query.count()
                    


def get_set_with_tracks(set_id):
    
    
    
    # Retrieve the set with the given ID along with its details
    set_instance:Set = Set.query.filter_by(id=set_id).first()
    if current_user.is_authenticated:
        playlist_from_set = db.session.query(Playlist).filter_by(set_id=set_id,user_id=current_user.id).first()
    else:
        playlist_from_set = None
    
    playlist_id = playlist_from_set.id if playlist_from_set else None
    
    if not set_instance:
        return {'error', 'Set not found'}
    
        # Fetch all TrackSet entries for this set
    track_sets = db.session.query(TrackSet).filter(TrackSet.set_id == set_id).all()
    

    # Create a dictionary mapping track_id to TrackSet details
    track_set_dict = [ {'id':ts.track_id,'start_time': ts.start_time, 'end_time': ts.end_time,'pos':ts.pos} for ts in track_sets]
    
    #tracks = db.session.query(TrackSet).options(joinedload(TrackSet.track)).filter_by(set_id=set_instance.id).all()
    tracks = [track_set.track for track_set in track_sets]
   
    tracks = format_db_tracks_for_template(tracks)
   
    tracks = format_tracks_with_times(tracks, track_set_dict)  
    tracks = sorted(tracks, key=lambda track: track['start_time'])
    channel = Channel.query.get(set_instance.channel_id)
    


    set_details = {
        'id': set_instance.id,
        'video_id': set_instance.video_id,
        'title': set_instance.title,
        'has_chapters':  set_instance.chapters is not None,
        #'description': set_instance.description,
        'duration': set_instance.duration,
        'publish_date': set_instance.publish_date,
        'thumbnail': set_instance.thumbnail,
        'channel_id': set_instance.channel_id,
        'channel': channel,
        'playlist_id':playlist_id,
        'playable_in_embed': set_instance.playable_in_embed,
        'nb_tracks': set_instance.nb_tracks,
        'tracks': tracks,
        'view_count': set_instance.view_count,
        'like_count': set_instance.like_count,
        'hidden': set_instance.hidden,
        
    }
    return set_details

def create_playlist(user_id, playlist_name,set_id=None):
    
    # Check for existing playlists with the same name
    existing_playlists = Playlist.query.filter(
        Playlist.user_id == user_id,
        func.lower(Playlist.title).like(func.lower(f"{playlist_name}%"))
    ).all()

    # If playlists with the same name exist, add a number suffix
    if existing_playlists:
        base_name = playlist_name
        count = 1
        while any(p.title.lower() == f"{playlist_name.lower()}" for p in existing_playlists):
            playlist_name = f"{base_name} ({count})"
            count += 1
    
    
    
    date_now = datetime.now(timezone.utc)
    new_playlist = Playlist(
          user_id=user_id,
          title=playlist_name,
          duration=0,
          create_date=date_now,
          edit_date=date_now,
          nb_tracks=0
      )
    if set_id:
        new_playlist.set_id = set_id
        
    db.session.add(new_playlist)
    db.session.commit()
    return new_playlist


def get_playlists_from_user(user_id, order_by='edit_date', search=None, page=1, per_page=10):
    # Define the valid columns for ordering
    valid_order_by_columns = {
        'create_date': Playlist.create_date.desc(),
        'edit_date': Playlist.edit_date.desc(),
        'az': Playlist.title.asc(),
        'duration': Playlist.duration.desc(),
        'nb_tracks': Playlist.nb_tracks.desc()
    }

    # Check if the provided order_by column is valid
    if order_by not in valid_order_by_columns:
        raise ValueError(f"Invalid order_by column: {order_by}. Valid options are: {', '.join(valid_order_by_columns.keys())}")

    # Get the column to order by
    order_column = valid_order_by_columns[order_by]

    # Start building the query
    query = Playlist.query.filter_by(user_id=user_id)

    # Add search filter if search term is provided
    if search:
        query = query.filter(Playlist.title.ilike(f"%{search}%"))

    # Apply ordering
    query = query.order_by(order_column)

    # Apply pagination
    paginated_query = query.offset((page - 1) * per_page).limit(per_page)

    # Return the result
    return paginated_query.all()



def get_playlist_last_used_from_user(user_id):
    return Playlist.query.filter_by(user_id=user_id).order_by(Playlist.edit_date.desc()).first()

def get_playlist_with_tracks(playlist_id):
    playlist = Playlist.query.get(playlist_id)
    
    if not playlist:
        return None
    
    tracks= format_db_tracks_for_template(playlist.tracks)
    
    tracks_playlist = db.session.query(TrackPlaylist).filter(TrackPlaylist.playlist_id == playlist_id).all()
    #track_playlist_dict = {tp.track_id: {'pos':tp.pos} for tp in tracks_playlist}
    track_playlist_dict = [ {'id':tp.track_id,'pos':tp.pos} for tp in tracks_playlist]
    
    
    tracks_with_pos = format_tracks_with_pos(tracks, track_playlist_dict)
    #pprint(tracks_ordered)
    tracks = sorted(tracks_with_pos, key=lambda track: track['pos'])
    playlist = {
        'id': playlist.id,
        'title': playlist.title,
        'duration': playlist.duration,
        'create_date': playlist.create_date,
        'edit_date': playlist.edit_date,
        'nb_tracks': playlist.nb_tracks,
        'playlist_id_spotify': playlist.playlist_id_spotify,
        'playlist_id_apple': playlist.playlist_id_apple,
        'set_id': playlist.set_id,
        'user_id': playlist.user_id,
        #'tracks': playlist.tracks
    }
    
    #return playlist

    return {'playlist': playlist, 'tracks': tracks}

def update_playlist_edit_date(playlist_id):
    playlist = Playlist.query.get(playlist_id)
    if playlist:
        playlist.edit_date = datetime.now(timezone.utc)
        db.session.commit()
        return True
    return False


def get_track_by_id(track_id,format_for_template=True):
    track = Track.query.get(track_id)
    if not track :
        return None
    if format_for_template:
        return format_db_track_for_template(track)
    return track


def add_track_to_playlist(playlist_id, track_id):

    # Fetch the playlist and track from the database
    try:
        playlist = Playlist.query.get(playlist_id)
        track = Track.query.get(track_id)

        if not playlist:
            return {"error": "Playlist not found"}
        if not track:
            return {"error": "Track not found"}

        existing_entry = TrackPlaylist.query.filter_by(playlist_id=playlist_id, track_id=track_id).first()
        
        if  existing_entry:         
            return {"error": f"Track was already in \"{playlist.title}\""}
        
        
        
        # Determine the position of the new track
        pos = db.session.query(db.func.max(TrackPlaylist.pos)).filter_by(playlist_id=playlist_id).scalar()
        pos = (pos or 0) + 1
        
        # Add track to playlist
        new_track_playlist_entry = TrackPlaylist(
        track_id=track.id,
        playlist_id=playlist.id,
        added_date=datetime.now(timezone.utc),
        pos=pos
        )

        db.session.add(new_track_playlist_entry)
        playlist.nb_tracks = len(playlist.tracks)
        
        playlist.edit_date = datetime.now(timezone.utc)
        playlist.duration = sum(track.duration_s or 0 for track in playlist.tracks)
        
        db.session.commit()
        
        #
        
        
    except Exception as e:
        return {"error": f"{str(e)} (playlist_id: {playlist_id}, track_id: {track_id})"}

   
    return {"message": f"Track added to \"{playlist.title}\""}


def change_playlist_title(playlist_id, new_title):
    
    # TODO : check if the title is not already taken by another playlist of the user
    try:
        
        existing_playlist = Playlist.query.filter_by(user_id=current_user.id, title=new_title).first()
        if existing_playlist:
            return {"error": "Title already taken by another playlist"}
        
        playlist = Playlist.query.get(playlist_id)
        if not playlist:
            return {"error": "Playlist not found"}
        
        playlist.title = new_title
        playlist.edit_date = datetime.now(timezone.utc)
        db.session.commit()
        return {"message": f"Playlist title changed to \"{new_title}\""}
    except Exception as e:
        return {"error": f"{str(e)} (playlist_id: {playlist_id})"}
   
    
# def delete_playlist(playlist_id):
#     try:
#         playlist = Playlist.query.filter_by(id=playlist_id,user_id=current_user.id).first()
#         db.session.delete(playlist)
#         db.session.commit()
#         return {"message": f"Playlist \"{playlist.title}\" deleted"}
#     except Exception as e:
#         return {"error": f"{str(e)} (playlist_id: {playlist_id})"}


def delete_playlist(playlist_id):
    try:
        # Find the playlist
        playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()
        
        if not playlist:
            return {"error": "Playlist not found"}

        # Delete related TrackPlaylist entries
        TrackPlaylist.query.filter_by(playlist_id=playlist_id).delete()
        
        # Delete the playlist
        db.session.delete(playlist)
        db.session.commit()
        
        return {"message": f"Playlist \"{playlist.title}\" deleted"}
    except Exception as e:
        db.session.rollback()  # Rollback in case of an error
        return {"error": f"{str(e)} (playlist_id: {playlist_id})"}

    
def tracks_to_tracks_ids(tracks):
    return [track['id'] for track in tracks]
 
    

def add_tracks_to_playlist(playlist_id, track_ids, user_id):
    
   
    

    try:
        logger.info('add_tracks_to_playlist')
        # Fetch the playlist from the database
        playlist = Playlist.query.get(playlist_id)
        if not playlist:
            logger.error('Playlist not found')
            return {"error": "Playlist not found"}
        
      
      # @TODO : veryfy against real tracks in db. Like are the tracks existing in the db ?
        
        unique_tracks_number = len(set(track_ids))
        # Fetch the tracks from the database
        tracks_in_db_count = Track.query.filter(Track.id.in_(track_ids)).count()
        
        are_counts_equal = unique_tracks_number == tracks_in_db_count
        
        if not are_counts_equal:
            logger.error('Tracks not found')
            return {"error": "One or more tracks was not found"}
        
        
        # Check for existing entries and add new ones
        existing_entries = TrackPlaylist.query.filter(TrackPlaylist.playlist_id == playlist_id).all()
        existing_track_ids = {entry.track_id for entry in existing_entries}
        
        
       # does not keep order mofo  
       # track_ids_to_add = list(set(track_ids) - set(existing_track_ids))

        
        pos = db.session.query(db.func.max(TrackPlaylist.pos)).filter_by(playlist_id=playlist_id).scalar()
        pos = (pos or 0) + 1
        
        # Remove duplicates while keeping the original order
        track_ids_to_add = [track_id for track_id in track_ids if track_id not in existing_track_ids]

        
        new_entries = []
        for track_id in track_ids_to_add:
            if track_id == 1 or track_id in existing_track_ids : # Unkown track, do not add it
                continue

            new_entry = TrackPlaylist(
                track_id=track_id,
                playlist_id=playlist_id,
                added_date=datetime.now(timezone.utc),
                pos=pos
            )
        
            new_entries.append(new_entry)
            pos += 1
        
   
        if new_entries:
            db.session.bulk_save_objects(new_entries)
            playlist.nb_tracks += len(new_entries)
            playlist.duration = sum(track.duration_s or 0 for track in playlist.tracks)
            playlist.edit_date = datetime.now(timezone.utc)
            db.session.commit()
            return {"message": f"{len(new_entries)} tracks added to \"{playlist.title}\""}
        else:
            return {"error": "No new tracks to add to the playlist"}

    except Exception as e:
        db.session.rollback()  # Rollback the session in case of an error
        return {"error": f"{str(e)} (playlist_id: {playlist_id})"}

    


def add_track_to_playlist_last_used(track_id, user_id):
    playlist = get_playlist_last_used_from_user(user_id)
    autocreated_playlist_message = ''
    if not playlist:
        # Create a new playlist if none exists
        playlist = create_playlist(user_id, "New Playlist")
        autocreated_playlist_message = "(A new playlist was created for you since none existed.)"
        
    
    ret = add_track_to_playlist(playlist.id, track_id)
    if 'message' in ret and autocreated_playlist_message:
        ret['message'] = f" {autocreated_playlist_message}" 
    return ret
    


def get_set_genres_by_occurrence(set_id):
    # Query to get the count of each genre
    genres_count = (
        db.session.query(
            Genre.name, 
            func.count(TrackGenres.genre_id).label('genre_count')
        )
        .join(TrackGenres, Genre.id == TrackGenres.genre_id)
        .join(Track, Track.id == TrackGenres.track_id)
        .join(TrackSet, Track.id == TrackSet.track_id)
        .filter(TrackSet.set_id == set_id)
        .group_by(Genre.name)
        .having(func.count(TrackGenres.genre_id) > 0)
        .order_by(func.count(TrackGenres.genre_id).desc())
        .all()
    )
    
    # Calculate the total count of all genres
    total_count = sum([genre.genre_count for genre in genres_count])
    
    # Calculate the percentage for each genre
    genres_percentage = [
        {
            'name': genre.name,
            'percentage': int( (genre.genre_count / total_count) * 100)
        }
        for genre in genres_count
    ]
    
    return genres_percentage


def get_set_avg_characteristics(set_id):
    characteristics = [
        'acousticness', 'danceability', 'energy',
        'liveness', 'loudness', 'instrumentalness', 'speechiness',
        'tempo',  'valence'
    ]
    
    # Building the query
    query = db.session.query(
        *[func.avg(getattr(Track, characteristic)).label(characteristic) for characteristic in characteristics]
    ).join(TrackSet, Track.id == TrackSet.track_id).filter(TrackSet.set_id == set_id)
    
    result = query.one()
    
    # Converting result to a dictionary
    avg_values = {characteristic: int(getattr(result, characteristic)) for characteristic in characteristics}

    return avg_values


def remove_track_from_playlist(playlist_id, track_id,user_id):

    playlist = Playlist.query.filter_by(id=playlist_id).first()
    if not playlist:
        return {"error": "Playlist not found"}
    
    track = Track.query.filter_by(id=track_id).first()
    if not track:
        return {"error": "Track not found"}
    
    track_playlist = db.session.query(TrackPlaylist).filter_by(playlist_id=playlist_id, track_id=track_id).first()
    if not track_playlist:
        return {"error": "Track not in playlist"}
    
    track_position = track_playlist.pos
    
    try:
        db.session.delete(track_playlist)
        playlist.nb_tracks = len(playlist.tracks)
        playlist.duration = sum(track.duration_s or 0 for track in playlist.tracks)
        playlist.edit_date = datetime.now(timezone.utc)
        
        db.session.query(TrackPlaylist).filter(
        TrackPlaylist.playlist_id == playlist_id,
        TrackPlaylist.pos > track_position
        ).update({TrackPlaylist.pos: TrackPlaylist.pos - 1}, synchronize_session='fetch')
        db.session.commit()
    except Exception as e:
        return {"error": f"{str(e)} (playlist_id: {playlist_id}, track_id: {track_id})"}
    
    return {"message": f"Track removed from \"{playlist.title}\""}


def update_playlist_positions_after_track_change_position( playlist_id: int, track_id: int, new_position: int):
    # Fetch the current position of the track
    track_playlist = db.session.query(TrackPlaylist).filter_by(playlist_id=playlist_id, track_id=track_id).first()
    current_position = track_playlist.pos
    
    # Update positions of the other tracks in the playlist
    if new_position < current_position:
        # Shift tracks down
        db.session.query(TrackPlaylist).filter(
            TrackPlaylist.playlist_id == playlist_id,
            TrackPlaylist.pos >= new_position,
            TrackPlaylist.pos < current_position
        ).update({TrackPlaylist.pos: TrackPlaylist.pos + 1}, synchronize_session='fetch')
    elif new_position > current_position:
        # Shift tracks up
        db.session.query(TrackPlaylist).filter(
            TrackPlaylist.playlist_id == playlist_id,
            TrackPlaylist.pos <= new_position,
            TrackPlaylist.pos > current_position
        ).update({TrackPlaylist.pos: TrackPlaylist.pos - 1}, synchronize_session='fetch')
    
    # Update the position of the moved track
    track_playlist.pos = new_position
    db.session.add(track_playlist)
    
    # Commit the changes
    db.session.commit()
    
    
def create_playlist_from_set_tracks(set_id, user_id):
    try:
        set_data = get_set_with_tracks(set_id)
        
        if 'error' in set_data:
            return set_data
        
        if 'tracks' not in set_data:
            return {"error": "No tracks found in set"}
        
        playlist_name = set_data.get('title', 'Untitled Playlist')
        new_playlist = create_playlist(user_id, playlist_name,set_id)
        
        if not new_playlist:
            return {"error": "Error creating playlist"}
        
        track_ids = tracks_to_tracks_ids(set_data['tracks'])
        
        
        
        response = add_tracks_to_playlist(new_playlist.id, track_ids, user_id)
        
        if 'error' in response:
            return {"error": response['error']}
        
    except KeyError as ke:
        return {"error": f"KeyError - missing key: {str(ke)}"}
    except TypeError as te:
        return {"error": f"TypeError - type mismatch: {str(te)}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}
    
    return {"message": f"Playlist \"{playlist_name}\" created successfully with {len(set_data['tracks'])} tracks", "playlist_id": new_playlist.id}


def add_all_tracks_from_set_to_playlist(set_id, playlist_id,user_id):
    try :
        set_data = get_set_with_tracks(set_id)
        if 'error' in set_data:
            return set_data
        
        if 'tracks' not in set_data:
            return {"error": "No tracks found in set"}
        
        track_ids = tracks_to_tracks_ids(set_data['tracks'])
        
        response = add_tracks_to_playlist(playlist_id, track_ids, user_id)
        
        if 'error' in response:
            return {"error": response['error']}
        
    except KeyError as ke:
        return {"error": f"KeyError - missing key: {str(ke)}"}
    except TypeError as te:
        return {"error": f"TypeError - type mismatch: {str(te)}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}
    
    return {"message": f"All tracks from set added to playlist"}    

def import_playlist_from_spotify():
    pass

def export_playlist_to_spotify():
    pass

def sync_playlist_with_spotify():
    pass


def spotify_tracks_uris_from_tracks(tracks):    
    return ['spotify:track:'+track['key_track_spotify'] for track in tracks if 'key_track_spotify' in track and track['key_track_spotify']]


def create_spotify_playlist_and_add_tracks(playlist_name, tracks,playlist_id):
    
    
    # check if playlist exists
    playlist = db.session.query(Playlist).filter_by(id=playlist_id,user_id=current_user.id).first()
   
    if not playlist:
        return {"error": "Playlist not found"}
    
    # does this playlist belong to user ?
    if playlist.user_id != current_user.id:
        return {"error": "Unauthorized access to this playlist"}
    

    # does this playlist exist on spotify ?
    
    
    try:
        # Create the Spotify playlist
        new_playlist = create_spotify_playlist(playlist_name)
        if not new_playlist:
            return {"error": "Error creating playlist"}
    except Exception as e:
        return {"error": f"Error creating playlist: {str(e)}"}
    
    
    playlist_id_spotify = new_playlist['id']
    db.session.query(Playlist).filter_by(id=playlist_id,user_id=current_user.id).update({Playlist.playlist_id_spotify: playlist_id_spotify})
    db.session.commit()
    try:
        # Extract track IDs
        track_ids = [track['key_track_spotify'] for track in tracks if 'key_track_spotify' in track and track['key_track_spotify']]
        
        if not track_ids:
            return {"error": "No valid track IDs found in the provided tracks"}

        response = add_tracks_to_spotify_playlist(new_playlist['id'], track_ids)
       
        if isinstance(response, dict) and 'error' in response:
            return {'error': response['error']}
    except KeyError as e:
        return {"error": f"Missing expected key in track data: {str(e)}"}
    except TypeError as e:
        return {"error": f"Type error encountered: {str(e)}"}
    except Exception as e:
        return {"error": f"Error adding tracks to playlist: {str(e)}"}

    return {"playlist_id":playlist_id,"spotify_playlist_id": new_playlist['id'],"message": f"Spotify playlist \"{playlist_name}\" created successfully with {len(track_ids)} tracks"}



def get_all_featured_set_searches():
    return db.session.query(SetSearch) \
        .filter(SetSearch.featured == True) \
            .order_by(SetSearch.query.asc()) \
            .all()


def get_random_set_searches(min_popularity, n):
   
    return db.session.query(SetSearch) \
        .filter(SetSearch.nb_results >= min_popularity) \
        .filter(SetSearch.featured == True) \
        .order_by(func.random()).limit(n).all()

def channel_toggle_followable(channel_id):
    channel = Channel.query.get(channel_id)
    if not channel:
        return {"error": "Channel not found"}
    
    # Toggle the followable status
    channel.followable = not channel.followable

    db.session.commit()
    return {"message":  f"channel_followable set to {channel.followable}"}


def channel_toggle_visibility(channel_id):
    channel = Channel.query.get(channel_id)
    if not channel:
        return {"error": "Channel not found"}
    
    channel.hidden = not channel.hidden
    # If the channel is hidden, set followable to False
    # But not necessary to set followable to True if channel is unhidden
    if channel.hidden:
        channel.followable = False
    db.session.commit()
    
    return {"message": f"Channel visibility toggled to {not channel.hidden}"}

def set_toggle_visibility(set_id):
    set_instance = Set.query.get(set_id)
    if not set_instance:
        return {"error": "Set not found"}
    
    set_instance.hidden = not set_instance.hidden
    db.session.commit()
   
    return {"message": f"Set visibility toggled to {not set_instance.hidden}"}


def get_channel_by_id(channel_id):
    channel = Channel.query.get(channel_id)
    if not channel:
        return None
    return channel

def get_channels(page=1, order_by='channel_popularity', per_page=20, hiddens=None):
    """
    Retrieves a paginated list of channels with customizable sorting and filtering options.

    Parameters:
    - page (int, optional): The page number of results to return. Defaults to 1.
    - order_by (str, optional): The order in which to return the channels. 
        - 'recent' (default): Orders by most recently created channels first (descending by creation date).
        - 'old': Orders by oldest channels first (ascending by creation date).
        - 'popular': Orders by channels with the most followers first (descending by follower count).
        - 'small_channel': Orders by channels with the fewest followers first (ascending by follower count).
    - per_page (int, optional): The number of results per page. Defaults to 20.
    - hiddens (bool, optional): If provided, filters channels by their hidden status (True for hidden, False for visible).

    Returns:
    - A paginated list of channels based on the specified criteria.

    Note:
    - The 'error_out=False' ensures that invalid page requests will return an empty result set rather than throwing an error.
    """

    
    query = Channel.query
    

    if order_by == 'az':
        query = query.order_by(Channel.author.asc())
    else:
        # as popularity is the default and only one other
        query = query.order_by(Channel.channel_follower_count.desc())
        
    if hiddens is not None:
        query = query.filter_by(hidden=hiddens)
    
    results = query.paginate(page=page, per_page=per_page, error_out=False)
    return results

def get_hidden_channels():
    return Channel.query.filter_by(hidden=True).all()

def get_channels_with_feat(feat):
    if feat == 'hidden':
        return get_hidden_channels()
    elif feat == 'not_followable':
        return Channel.query.filter_by(followable=False).all()
    elif feat == 'followable':
        return Channel.query.filter_by(followable=True).all()
    elif feat == 'not_hidden':
        return Channel.query.filter_by(hidden=False).all()
    else:
        return {'error': 'Invalid feat'}

def get_unfollowable_channels():
    return Channel.query.filter_by(followable=False).all()

def get_hidden_sets():
    return Set.query.filter_by(hidden=True).all()


def get_set_searches(featured=None, sort_by="nb_results", page=1, per_page=200):
    
    # Start with the base query
    query = db.session.query(SetSearch)
    
    # Add a filter if 'featured' is not None
    if featured is not None:
        query = query.filter(SetSearch.featured == featured)
    
    # Apply ordering and pagination
    results = query.order_by(getattr(SetSearch, sort_by).desc()) \
                   .paginate(page=page, per_page=per_page, error_out=False)
    
    return results

    
    return results

def search_toggle_featured(set_search_id):
    set_search = db.session.query(SetSearch).get(set_search_id)
    if not set_search:
        return {"error": "Set search not found"}
    
    set_search.featured = not set_search.featured
    db.session.commit()
    
    return {"message": f"Set search featured status toggled to {set_search.featured}"}



def get_app_config_key(key):
    key = key.lower().strip()
    config = AppConfig.query.filter_by(key=key).first()
    if config:
        return config.value
    return None

def set_app_config_key(key, value):
    key = key.lower().strip()
    app_config = AppConfig.query.filter_by(key=key).first()
    if app_config:
        app_config.value = value
    else:
        app_config = AppConfig(key=key, value=value)
        db.session.add(app_config)
    db.session.commit()
    return app_config

def remove_app_config_key(key):
    key = key.upper().strip()
    app_config = AppConfig.query.filter_by(key=key).first()
    if app_config:
        db.session.delete(app_config)
        db.session.commit()
        return True
    return False


# Function to generate Apple Music Developer Token
def _generate_apple_music_dev_token():
    headers = {
        'alg': 'ES256',
        'kid': APPLE_KEY_ID
    }
    payload = {
        'iss': APPLE_TEAM_ID,
        'iat': int(time.time()),
        'exp': int(time.time()) + APPLE_TOKEN_EXPIRY_LENGTH,
        'aud': 'appstoreconnect-v1'
    }
    token = jwt.encode(payload, APPLE_PRIVATE_KEY, algorithm='ES256', headers=headers)
    set_app_config_key('apple_music_dev_token', token)
    set_app_config_key('apple_music_dev_token_expiry', int(time.time()) + APPLE_TOKEN_EXPIRY_LENGTH)
    return token

def get_apple_music_dev_token():
    # Get the current token
    token_value = get_app_config_key('apple_music_dev_token')
    if token_value:
        token_expiry = get_app_config_key('apple_music_dev_token_expiry')
        
        # Check if the token is expired
        if token_expiry and int(token_expiry) + APPLE_TOKEN_EXPIRY_LENGTH - 3600 < time.time():
            return token_value
   
    # token expired or not set, generate a new one
    new_token = _generate_apple_music_dev_token()
    return new_token



def get_user_extra_field(user, field):
    if not user.is_authenticated:
        
        return None 
   
    if user.extra_fields:
        return user.extra_fields.get(field, None)
    return None

def set_user_extra_field(user,field, value):
    
    if not user.is_authenticated:
        return False
    
    if not user.extra_fields or user.extra_fields is None:
        #user.extra_fields = {}  # Initialize as empty dictionary if None
        user.extra_fields = MutableDict()
    user.extra_fields[field] = value  # Set or update the field with the provided value
    
   
    try:
        
        db.session.commit()  # Commit the change to the database
        return True
    except Exception as e:
        db.session.rollback()
        #print(f'Error during commit: {e}')
        return False
  
   
   
def get_apple_music_user_token():
    token = get_user_extra_field(current_user, 'apple_music_user_token')
    if not token:
        return None
    return token


def set_apple_music_user_token(user,token):
    return set_user_extra_field(user, 'apple_music_user_token', token)

def remove_user_extra_field(user, field):
    if not user.is_authenticated:
        return None 
    
    if user.extra_fields and field in user.extra_fields:
        user.extra_fields.pop(field)  # Remove the field from the JSON
        db.session.commit()  # Commit the change to the database
        return True
    
    return False


def update_playlist_field(playlist,field,value):
    db.session.query(Playlist).filter_by(id=playlist['id']).update({field: value})
    db.session.commit()
    return True



def apple_playlist_exists(dev_token, user_token, playlist_id):
    url = f'https://api.music.apple.com/v1/me/library/playlists/{playlist_id}'

    headers = {
        'Authorization': f'Bearer {dev_token}',
        'Music-User-Token': user_token,
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)

    # Check if playlist exists
    if response.status_code == 200:
        playlist_data = response.json()

        # Check if 'data' is present and has at least one item
        if 'data' in playlist_data and len(playlist_data['data']) > 0:
            attributes = playlist_data['data'][0]['attributes']
            
            # Check if playlist has been deleted based on 'canEdit' and 'lastModifiedDate' values
            if attributes.get('canEdit') == False and attributes.get('lastModifiedDate') == '1970-01-01T00:00:00Z':
                
                return False
            else:
                
                return True
        else:
            
            return False

    # Handle 404 not found
    elif response.status_code == 404:
        
        return False

    # Handle other errors
    else:
        # print(f"Error: {response.status_code}")
        # print(response.text)
        return None


# Function to create a playlist for the user
def create_apple_playlist(dev_token, user_token, playlist_name, playlist_description=""):
    

    url = 'https://api.music.apple.com/v1/me/library/playlists'
    playlist_data = {
        "attributes": {
            "name": playlist_name,
            "description": playlist_description,
        }
    }

    headers = {
        'Authorization': f'Bearer {dev_token}',
        'Music-User-Token': user_token,
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=json.dumps(playlist_data))
    
    if response.status_code == 201:
        
        playlist = response.json()
        playlist_data = playlist['data'][0]
        return playlist_data  # Playlist details
    else:
        # print(f"Error: {response.status_code}")
        # print(response.text)
        return None
    
    
def get_track_ids_from_apple_playlist(dev_token,user_token,playlist_id):
    
    url = f'https://api.music.apple.com/v1/me/library/playlists/{playlist_id}/tracks'
    headers = {
        'Authorization': f'Bearer {dev_token}',
        'Music-User-Token': user_token,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            tracks_data = response.json()

            try:
                track_ids = [track['attributes']['playParams']['catalogId'] for track in tracks_data['data']]
            except Exception as e:
                logger.error(f"Error extracting track IDs: {str(e)}")
                track_ids = []

            
        else:
            # print(f"Error: {response.status_code} (in get_track_ids_from_apple_playlist)")
            # print(response.text)
            track_ids = []
        
    except Exception as e:
        return(f"Error: {str(e)} (in get_track_ids_from_apple_playlist)")
        
    return track_ids

def add_tracks_to_apple_playlist(dev_token,user_token,playlist_id, track_ids):
    """
    Adds tracks to a specified Apple Music playlist.

    Parameters:
    - dev_token: str, Developer Token for Apple Music API.
    - user_token: str, User Token obtained from MusicKit JS or similar.
    - playlist_id: str, The ID of the playlist to which tracks should be added.
    - track_ids: list of str, A list of track IDs to be added to the playlist.

    Returns:
    - response: dict, Response from the Apple Music API.
    """
    # Apple Music API endpoint for adding tracks to a playlist
    url = f'https://api.music.apple.com/v1/me/library/playlists/{playlist_id}/tracks'
    
    # Create the data payload for the request
    track_data = {
        "data": [{"id": track_id, "type": "songs"} for track_id in track_ids]
    }
    

    
    # Headers for the API request
    headers = {
        'Authorization': f'Bearer {dev_token}',
        'Music-User-Token': user_token,
        'Content-Type': 'application/json'
    }
    
    # Make the POST request to add tracks to the playlist
    try:
        response = requests.post(url, headers=headers, data=json.dumps(track_data))
    except Exception as e:
        return {"error": f"Error adding tracks: {str(e)}"}
    
    
    
    # Check if the request was successful
    if response.status_code == 204:
        return {"message": f"{len(track_ids)} tracks added to playlist"}
    elif response.status_code == 404:
        return []
    else: 
        response_json = response.json()
        if 'errors' in response_json:
            error_details = response_json['errors'][0]
            return {"error": f'{error_details["title"]} - {error_details["detail"]}'}
        
        return {"error": response.text}
    
def create_apple_playlist_and_add_tracks(dev_token,user_token,playlist_name, tracks,playlist):
    
    
    # check if playlist exists
    
   
    if not playlist:
        return {"error": "Playlist not found"}
    
    # does this playlist belong to user ?
    if playlist.get('user_id') != current_user.id:
        return {"error": "Unauthorized access to this playlist"}
    
    track_ids = [track['key_track_apple'] for track in tracks if 'key_track_apple' in track and track['key_track_apple']]
    if not track_ids:
        return {"error": "No valid Apple track IDs found in the provided tracks"}
    
    is_new_playlist = False
    # does this playlist exist on apple ?
    if not playlist.get('playlist_id_apple'):
        is_new_playlist = True
        try:
            # Create the Spotify playlist
            new_playlist = create_apple_playlist(dev_token,user_token,playlist_name,'Created from Set2Tracks')
            
            if not new_playlist:
                return {"error": "Error creating playlist"}
        except Exception as e:
            return {"error": f"Error creating playlist: {str(e)}"}
        
        playlist_id_apple = new_playlist['id']
        existing_tracks_ids = []
    else:
        playlist_id_apple = playlist.get('playlist_id_apple')
        playlist_still_exists = apple_playlist_exists(dev_token,user_token,playlist_id_apple)
        if not playlist_still_exists:
            update_playlist_field(playlist, 'playlist_id_apple',None)
            playlist['playlist_id_apple'] = None # update the playlist object as well
            return create_apple_playlist_and_add_tracks(dev_token,user_token,playlist_name, tracks,playlist)
        
        existing_tracks_ids = get_track_ids_from_apple_playlist(dev_token,user_token,playlist_id_apple)        
    
    if len(existing_tracks_ids) > 0:
        track_ids_to_add = list(set(track_ids) - set(existing_tracks_ids))
    else:
        track_ids_to_add = track_ids
        

            
    if len(track_ids_to_add) == 0:
        return {"error": "No new tracks to add to the playlist"}
    
    update_playlist_field(playlist, 'playlist_id_apple',playlist_id_apple)
    try:

        response = add_tracks_to_apple_playlist(dev_token,user_token,playlist_id_apple, track_ids_to_add)

        
        
        if 'error' in response:
            return {'error': response['error'],'track_ids':track_ids}
    except KeyError as e:
        return {"error": f"Missing expected key in track data: {str(e)}"}
    except TypeError as e:
        return {"error": f"Type error encountered: {str(e)}"}
    except Exception as e:
        return {"error": f"Error adding tracks to playlist: {str(e)}"}

    if is_new_playlist:
        return {"playlist_id":playlist['id'],"apple_playlist_id": playlist_id_apple,"message": f"Apple playlist \"{playlist_name}\" created successfully with {len(track_ids_to_add)} tracks"}
    else:
        return {"playlist_id":playlist['id'],"apple_playlist_id": playlist_id_apple,"message": f"Apple playlist \"{playlist_name}\" updated successfully with {len(track_ids_to_add)} tracks"}



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
