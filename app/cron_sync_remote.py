
from requests import get
from web.model import Genre, Set, Channel, TrackSet, Track, TrackGenres

import logging

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.session import make_transient

from web import create_app
from boilersaas.utils.db import db


from web.model import SetQueue

# TODO the loop
# Update set queue too
# UPdate fields like nb_sets etc.

logger = logging.getLogger('root')
logger.info('Sync Worker started')

def get_or_create(session_to, session_from, model, source_obj, preserve_id=False, find_by=None):
    """
    Retrieves a record from `session_to` or creates it using data from `session_from` without committing.
    
    Args:
        session_to: SQLAlchemy session where the new object will be stored.
        session_from: SQLAlchemy session where the source object exists.
        model: The SQLAlchemy model class (e.g., Channel).
        source_obj: The object from session_from to copy data from.
        preserve_id (bool): If True, preserves the original ID; otherwise, lets DB auto-generate it.
        find_by (dict, optional): A dictionary of column-value pairs to search for an existing record.
                                  If provided, the function queries using these filters instead of the primary key.

    Returns:
        The retrieved or newly created model instance (with an ID if newly created).
    """
    try:
        primary_key_columns = [column.name for column in inspect(model).primary_key]
        primary_key_column = primary_key_columns[0]  # Use only the first primary key
        primary_key_value = getattr(source_obj, primary_key_column)

        # Check if the record already exists in the target session
        if find_by:
            record = session_to.query(model).filter_by(**find_by).first()
        else:
            record = session_to.query(model).filter(getattr(model, primary_key_column) == primary_key_value).first()

        if record:
            logger.info(f'{model.__name__} found in target session, updating')
        else:
            logger.info(f'No {model.__name__} not found in target session, creating a new one')

            # Detach and copy attributes from source session
            record_data = {
                column.name: getattr(source_obj, column.name)
                for column in model.__table__.columns
                if preserve_id or column.name != primary_key_column  # Skip ID if not preserving
            }

            # Manually assign ID only if preserving it
            if preserve_id:
                record_data[primary_key_column] = primary_key_value
                
            logger.info(f'Creating {model.__name__} with data: {record_data}')

            # Create a new instance in the target session
            record = model(**record_data)
            session_to.add(record)
            session_to.flush()  # Assigns an ID without committing

            # PostgreSQL: Reset sequence if preserving ID
            if preserve_id and session_to.bind.dialect.name == "postgresql":
                session_to.execute(
                    text(
                        f"SELECT setval(pg_get_serial_sequence(:table, :column), "
                        f"(SELECT COALESCE(MAX({primary_key_column}), 1) FROM {model.__tablename__}))"
                    ),
                    {"table": model.__tablename__, "column": primary_key_column}
                )
                session_to.flush()
    except Exception as e:
        logger.error(f'Error creating {model.__name__}: {e}, {source_obj}')
        raise e

    return record



## TODO : the loop
## Missing genres.

def worker_set_queue():
    app = create_app()
    
    session_from = db.session
    
    secondary_engine = create_engine(app.config['SQLALCHEMY_DATABASE2_URI'], pool_recycle=3600)
    session_to = scoped_session(sessionmaker(bind=secondary_engine))
    session_to.flush()
    
    with app.app_context():
       
        
       
        last_updated_set_time_online = session_to.query(Set).order_by(Set.updated_at.desc()).first().updated_at
        nb_sets_to_sync = session_from.query(Set).filter(Set.updated_at > last_updated_set_time_online).count()
        logger.info(f'{nb_sets_to_sync} sets to sync')
        
        # while nb_sets_to_sync > 0:
        set_to_sync_from = session_from.query(Set).filter(Set.updated_at > last_updated_set_time_online).order_by(Set.updated_at.asc()).first()
        
        
        ## channel from set_to_sync_from
        channel_to_sync_from = session_from.query(Channel).filter(Channel.id == set_to_sync_from.channel_id).first()
        
        
        try:
            channel = get_or_create(session_to,session_from, Channel, channel_to_sync_from, preserve_id=True)

            set_ = get_or_create(session_to,session_from, Set, set_to_sync_from, preserve_id=True)

            print('Set:', set_)
            print('Channel:', channel)

            track_sets = session_from.query(TrackSet).filter(TrackSet.set_id == set_to_sync_from.id).all()
            tracks = [track_set.track for track_set in track_sets]
            track_map = {}  # Maps key_track_shazam -> new track ID in secondary DB
            for track in tracks:
                
                genres = track.genres
                for genre in genres:
                    genre = get_or_create(session_to,session_from, Genre, genre, preserve_id=False,find_by={'name':genre.name})
                    track_genre_dict = {'track_id':track.id,'genre_id':genre.id}
                    track_genre_obj = TrackGenres(**track_genre_dict)
                    logger.info(f"Adding Genre with track_id: {track_genre_obj.track_id} and genre_id: {track_genre_obj.genre_id}")
                    track_genre = get_or_create(session_to,session_from, TrackGenres, track_genre_obj, preserve_id=True,find_by=track_genre_dict)
                    
                track.genres = genres
                
                track = get_or_create(session_to,session_from, Track, track, preserve_id=False,find_by={'key_track_shazam':track.key_track_shazam})
                #logger.info(f'Track {track.id} - {track.title} added')
                track_map[track.key_track_shazam] = track.id

            for track_set in track_sets:
                track_set.track_id = track_map[track_set.track.key_track_shazam]
                
                logger.info(f"Adding TrackSet with track_id: {track_set.track_id}, set_id: {track_set.set_id}, start_time: {track_set.start_time}, end_time: {track_set.end_time}, pos: {track_set.pos}")

                track_set = get_or_create(session_to,session_from, TrackSet, track_set, preserve_id=True,find_by={'set_id':track_set.set_id,'track_id':track_set.track_id,'pos':track_set.pos})

            session_to.commit()
        except Exception as e:
            logger.error(f'Error syncing set {set_to_sync_from.id}: {e}')
            session_to.rollback()
            
            
        
        
        
        
        
            


if __name__ == '__main__':
    worker_set_queue()

    
    