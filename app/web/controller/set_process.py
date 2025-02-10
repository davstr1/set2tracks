


import os
import shutil
import traceback
from web.controller.set import validate_set_data
from web.controller.utils import error_out
import json
from web.lib.count_unique_tracks import count_unique_tracks
from web.lib.audio import cut_audio
from web.lib.av_apis.apple import add_apple_track_data_from_json
from web.lib.av_apis.shazam import sync_process_segments
from web.lib.av_apis.spotify import add_tracks_spotify_data_from_json
from web.lib.av_apis.youtube import download_youtube_video
from web.lib.format import prepare_track_for_insertion
from web.lib.process_shazam_json import write_deduplicated_segments, write_segments_from_chapter
from web.lib.utils import calculate_avg_properties
from web.controller.channel import get_or_create_channel
from web.model import RelatedTracks, Set, Track, TrackSet
from datetime import datetime,timezone
from boilersaas.utils.db import db
from web.logger import logger
from sqlalchemy.exc import SQLAlchemyError

AUDIO_SEGMENTS_LENGTH = int(os.getenv('AUDIO_SEGMENTS_LENGTH'))#


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
        
        logger.info(f'Processing segments from {dedup_segments_filepath}')
    
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
        
        logger.info(f'Adding {len(songs)} tracks to set {set.id}')
        
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
      
      
