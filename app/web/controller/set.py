import json
from flask import url_for
from flask_login import current_user
from sqlalchemy import func, or_
from web.model import Genre, Playlist, Set, SetBrowsingHistory, SetQueue, Channel, SetSearch, Track, TrackGenres, TrackSet
from web.lib.format import format_db_tracks_for_template, format_tracks_with_times
from datetime import datetime,timezone,timedelta
from boilersaas.utils.db import db
import re
from web.logger import logger
from web.controller.utils import sanitize_query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

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
        
     
def get_playable_sets(page=1, per_page=20, search=None, order_by='latest_youtube', deduplicate=False):
    prefixed_search = False
    
    if search or page > 1:
        deduplicate = False

    if search and search.startswith('trackid:'):
        track_id = search[len('trackid:'):]
        # TODO check for numeric value
        prefixed_search = True
        query = (
            Set.query.filter_by(playable_in_embed=True, published=True, hidden=False)
            .join(TrackSet, Set.id == TrackSet.set_id)
            .join(Set.channel)
            .filter(Set.channel.has(hidden=False))
            .options(joinedload(Set.channel))
            .filter(TrackSet.track_id == track_id)
        )

    elif search and search.startswith('channelid:'):
        channel_id = search[len('channelid:'):]
        prefixed_search = True
        query = Set.query.filter_by(playable_in_embed=True, published=True, hidden=False, channel_id=channel_id)

    else:
        query = (
            Set.query.filter_by(playable_in_embed=True, published=True, hidden=False)
            .join(Set.channel)
            .filter(Set.channel.has(hidden=False))
            .options(joinedload(Set.channel))
        )

    if search and not prefixed_search:
        search_filter = or_(
            Set.title_tsv.match(search),  # Assuming title_tsv is a full-text search vector
            Channel.author.match(search)  # Assuming author is also a searchable field
        )
        query = query.filter(search_filter)

    if order_by == 'latest_youtube':
        query = query.order_by(Set.publish_date.desc())
    elif order_by == 'latest_set2tracks':
        query = query.order_by(Set.id.desc())
    elif order_by == 'channel_popularity':
        query = query.order_by(Channel.channel_follower_count.desc())

    results_count = query.count()
    paginated_results = query.paginate(page=page, per_page=per_page, error_out=False)

    if deduplicate:
        results = paginated_results.items
        deduplicated_results = []
        channel_seen = {}

        for result in results:
            channel_id = result.channel_id
            if channel_id not in channel_seen:
                channel_seen[channel_id] = 1
                result.show = 1
                result.nb_other_sets_from_channel = 0
                deduplicated_results.append(result)
            else:
                channel_seen[channel_id] += 1

        for result in deduplicated_results:
            result.nb_other_sets_from_channel = channel_seen[result.channel_id] - 1

        # Replace only the items in the current page
        paginated_results.items = deduplicated_results

    if search and not prefixed_search:
        upsert_setsearch(search, results_count)

    return paginated_results, results_count


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
    


    try:
        set_queue_entry = SetQueue.query.filter_by(video_id=set_instance.video_id).first()
        if set_queue_entry and set_queue_entry.video_info_json:
            print('set_queue_entry.video_info_json',set_queue_entry.video_info_json)
            video_info_json = set_queue_entry.video_info_json
        else:
            video_info_json = {}  
    except json.JSONDecodeError:
        video_info_json = {}  
    except Exception as e:
        video_info_json = {}  
        logger.error(f"An error occurred with the video_info: {e}")
        
    upload_date_str = video_info_json.get('upload_date', datetime.now().strftime("%Y%m%d"))
    upload_date = f"{upload_date_str[:4]}-{upload_date_str[4:6]}-{upload_date_str[6:]}"
    utc_date = datetime.strptime(upload_date, "%Y-%m-%d").replace(hour=8, minute=0, second=0, tzinfo=timezone.utc) # 8am UTC, yep.
    upload_date_iso = utc_date.isoformat()
    
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
        'video_info_json': video_info_json,
        'upload_date': upload_date_iso
        
    }
    return set_details
  
  
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



def set_toggle_visibility(set_id):
    set_instance = Set.query.get(set_id)
    if not set_instance:
        return {"error": "Set not found"}
    
    set_instance.hidden = not set_instance.hidden
    db.session.commit()
   
    return {"message": f"Set visibility toggled to {not set_instance.hidden}"}



def get_hidden_sets():
    return Set.query.filter_by(hidden=True).all()