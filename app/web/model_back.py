#from boilersaas.routes import User
from boilersaas.utils.db import db
from datetime import datetime, timezone
from sqlalchemy import DDL, Index, JSON,  Integer,SmallInteger, func
from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils.types import TSVectorType
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy_searchable import search
#from flask import current_app as app


Base = declarative_base()

# Association table for the many-to-many relationship between Track and Genre
class TrackGenres(db.Model):
    __tablename__ = 'track_genres'
    track_id = db.Column(Integer, db.ForeignKey('tracks.id'), primary_key=True)
    genre_id = db.Column(Integer, db.ForeignKey('genres.id'), primary_key=True)


class Genre(db.Model):
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    track_count = db.Column(db.Integer, default=0, nullable=False)
    tracks = db.relationship('Track', secondary='track_genres', back_populates='genres')
    
    def __repr__(self):
        return f"<Genre {self.id}: {self.name}>"

class RelatedTracks(db.Model):
    __tablename__ = 'related_tracks'
    track_id = db.Column(db.Integer, db.ForeignKey('tracks.id'), primary_key=True)
    related_track_id = db.Column(db.Integer, db.ForeignKey('tracks.id'), primary_key=True)
    insertion_order = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.Index('idx_insertion_order', 'track_id', 'insertion_order'),
    )

  
 
class Track(db.Model):
    __tablename__ = 'tracks'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    key_track_shazam = db.Column(db.Integer, unique=True, index=True)
    key_track_spotify = db.Column(db.String(255),unique=True,  index=True)
    key_track_apple = db.Column(db.String(255),unique=True,  index=True)
    
    key_artist_spotify = db.Column(db.String(255), index=True)
    key_artist_apple = db.Column(db.String(255), index=True)

    title = db.Column(db.String(255), nullable=False, index=True)
    artist_name = db.Column(db.String(255), index=True)
    album = db.Column(db.String(255))
    label = db.Column(db.String(255), index=True)
    
    cover_arts = db.Column(JSON)  # Consolidated cover art URIs
    preview_uris = db.Column(JSON)  # Consolidated preview URIs
    uri_apple = db.Column(db.String(255))
    release_year = db.Column(db.Integer, index=True)
    release_date = db.Column(db.Date, nullable=True, index=True)
    artist_popularity_spotify = db.Column(db.Integer, index=True)
    
    nb_sets = db.Column(db.Integer, default=0, index=True)
    nb_playlists = db.Column(db.Integer, default=0, index=True)
    #sets = db.relationship('Set', secondary='track_sets', back_populates='tracks')
    playlists = db.relationship('Playlist', secondary='track_playlists', back_populates='tracks',overlaps="playlists,tracks")
    genres = db.relationship('Genre', secondary='track_genres', back_populates='tracks')
    related_tracks_checked = db.Column(db.Boolean, default=False)
    related_tracks = db.relationship(
        'Track',
        secondary='related_tracks',
        primaryjoin=id == RelatedTracks.track_id,
        secondaryjoin=id == RelatedTracks.related_track_id,
        order_by=RelatedTracks.insertion_order,
        backref=db.backref('related_to', order_by=RelatedTracks.insertion_order)
    )
    
    # Spotify API fields
    
    acousticness = db.Column(SmallInteger, index=True)
    danceability = db.Column(SmallInteger, index=True)
    duration_s = db.Column(Integer, index=True)
    energy = db.Column(SmallInteger, index=True)
    key = db.Column(SmallInteger, index=True) # 1-11
    mode = db.Column(SmallInteger, index=True) # 0-1
    liveness = db.Column(SmallInteger, index=True)
    loudness = db.Column(SmallInteger, index=True)
    instrumentalness = db.Column(SmallInteger, index=True)
    speechiness = db.Column(SmallInteger, index=True)
    tempo = db.Column(SmallInteger, index=True)
    time_signature = db.Column(SmallInteger, index=True)
    valence = db.Column(SmallInteger, index=True)
    
    search_vector = db.Column(TSVectorType('title', 'artist_name'))
    
    def has_related_tracks(self):
        return bool(self.related_tracks)

    __table_args__ = (
        Index('ix_tracks_search_vector', 'search_vector', postgresql_using='gin'),
    )




# https://www.youtube.com/feeds/videos.xml?channel_id=THE_CHANNEL_ID_HERE

class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    channel_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    nb_sets = db.Column(db.Integer, default=0, index=True)
    author = db.Column(db.String(255), index=True)
    channel_url = db.Column(db.String(255))
    channel_follower_count = db.Column(db.Integer)
    sets = db.relationship('Set', backref='channel', lazy=True)  # completed this line
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    hidden = db.Column(db.Boolean, default=False, index=True)
    followable = db.Column(db.Boolean, default=False, index=True)
        

class Set(db.Model):
    __tablename__ = 'sets'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    video_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # completed this line  
    title = db.Column(db.String(255), nullable=False, index=True)
    title_tsv = db.Column(TSVectorType)

    duration = db.Column(db.Integer, index=True)  # in seconds
    #publish_date = db.Column(db.DateTime, index=True)  # Assuming this maps to 'upload_date'
    publish_date = db.Column(db.Date, index=True)
    published = db.Column(db.Boolean, default=False, index=True)
    thumbnail = db.Column(db.String(255))  # URL to the thumbnail image
    playable_in_embed = db.Column(db.Boolean)
    chapters = db.Column(db.JSON)  # JSON object for chapters if not None
    nb_tracks = db.Column(db.Integer, default=0, index=True)
    like_count = db.Column(db.Integer, default=0,nullable=False, index=True)
    view_count = db.Column(db.Integer, default=0,nullable=False, index=True)
    decades = db.Column(db.ARRAY(db.Integer), nullable=True)
    
    artist_popularity_spotify = db.Column(SmallInteger)
    acousticness = db.Column(SmallInteger)
    danceability = db.Column(SmallInteger)
    energy = db.Column(SmallInteger)
    liveness = db.Column(SmallInteger)
    loudness = db.Column(SmallInteger)
    instrumentalness = db.Column(SmallInteger)
    speechiness = db.Column(SmallInteger)
    valence = db.Column(SmallInteger)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    error = db.Column(db.Text, nullable=True)
    hidden = db.Column(db.Boolean, default=False, index=True)
   # tracks = db.relationship('Track', secondary='track_sets', back_populates='sets')
   
class SetSearch(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    query = db.Column(db.String(255), nullable=False)
    nb_results = db.Column(db.Integer, nullable=False)
    featured = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class SetBrowsingHistory(db.Model):
    __tablename__ = 'set_browsing_history'
    
    set_id = db.Column(db.Integer, db.ForeignKey('sets.id'), primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now())
    
    __table_args__ = (
        db.UniqueConstraint('set_id', 'user_id', name='uq_set_user'),  # Ensures no duplicates
        db.Index('ix_set_user_datetime', 'set_id', 'user_id', 'datetime'),  # For performance
    )
   

class SetQueue(db.Model):
    __tablename__ = 'set_queue'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    video_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user_premium = db.Column(db.Boolean, default=False)
    status = db.Column(ENUM('premiered','prequeued','pending', 'processing', 'done', 'discarded', 'failed', name='status_enum'), nullable=False, default='prequeued')
    queued_at = db.Column(db.DateTime(timezone=True), nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    premiere_ends = db.Column(db.DateTime(timezone=True), nullable=True, default=None) 
    n_attempts = db.Column(db.Integer, nullable=False, default=1)  # New field
    discarded_reason = db.Column(db.String(255))
    video_info_json = db.Column(db.JSON)
    duration = db.Column(db.Integer, index=True)  # in seconds
    nb_chapters = db.Column(db.Integer, default=0, index=True)
    send_email = db.Column(db.Boolean, default=False, index=True)
    play_sound = db.Column(db.Boolean, default=False, index=True)
    notification_email_sent = db.Column(db.Boolean, default=False, index=True)
    notification_sound_sent = db.Column(db.Boolean, default=False, index=True)

    
    
class Playlist(db.Model):
    __tablename__ = 'playlists'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # completed this line 
    playlist_id_spotify = db.Column(db.String(255),  unique=True, index=True)
    playlist_id_apple = db.Column(db.String(255),  unique=True, index=True)
    set_id = db.Column(db.Integer, db.ForeignKey('sets.id'), nullable=True,index=True)  # completed this line
    title = db.Column(db.String(255), nullable=False, index=True)
    search_vector = db.Column(TSVectorType('title'))
    
    duration = db.Column(db.Integer, index=True)  # in seconds
    create_date = db.Column(db.DateTime, index=True)  # Assuming this maps to 'upload_date'
    edit_date = db.Column(db.DateTime, index=True)  # Assuming this maps to 'upload_date'
    nb_tracks = db.Column(db.Integer, default=0, index=True)
    
    artist_popularity_spotify = db.Column(SmallInteger)
    acousticness = db.Column(SmallInteger)
    danceability = db.Column(SmallInteger)
    energy = db.Column(SmallInteger)
    liveness = db.Column(SmallInteger)
    loudness = db.Column(SmallInteger)
    instrumentalness = db.Column(SmallInteger)
    speechiness = db.Column(SmallInteger)
    valence = db.Column(SmallInteger)
    
    __table_args__ = (
        Index('ix_playlists_search_vector', 'search_vector', postgresql_using='gin'),
    )
    
    track_associations = db.relationship('TrackPlaylist', back_populates='playlist', cascade="all, delete-orphan",overlaps='playlists')
    tracks = db.relationship('Track', secondary='track_playlists', back_populates='playlists',overlaps="track_associations")
    



class TrackSet(db.Model):
    __tablename__ = 'track_sets'
    track_id = db.Column(db.Integer, db.ForeignKey('tracks.id'), primary_key=True)
    set_id = db.Column(db.Integer, db.ForeignKey('sets.id'), primary_key=True)
    start_time = db.Column(db.Integer)  # in seconds
    end_time = db.Column(db.Integer)    # in seconds
    pos = db.Column(db.Integer, primary_key=True)  # position in the set, now part of the primary key
    track = db.relationship('Track', backref='track_sets')  # Add this relationship
    set = db.relationship('Set', backref='track_sets')  
    
class TrackPlaylist(db.Model):
    __tablename__ = 'track_playlists'
    track_id = db.Column(db.Integer, db.ForeignKey('tracks.id'), primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id',ondelete='CASCADE'), primary_key=True)
    added_date = db.Column(db.DateTime, index=True)  
    pos = db.Column(db.Integer, primary_key=True)  
    
    track = db.relationship('Track', backref='track_playlists',overlaps="playlists,tracks")
    playlist = db.relationship('Playlist', back_populates='track_associations',overlaps="playlists,tracks")
    
    
class AppConfig(db.Model):
    __tablename__ = 'app_config'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    key = db.Column(db.String(255), nullable=False, unique=True)
    value = db.Column(db.String(1024), nullable=False)

@listens_for(Track.genres, 'append')
def receive_after_insert(target, value, initiator):
    genre = value  # Here, value is the Genre instance being added to the Track
    genre.track_count += 1
    # No commit here, just modify the state


@listens_for(Track.genres, 'remove')
def receive_after_remove(target, value, initiator):
    genre = value  # Here, value is the Genre instance being removed from the Track
    genre.track_count -= 1
    
# Event listener for updating search_vector
@listens_for(Track, 'before_insert')
@listens_for(Track, 'before_update')
def update_search_vector(mapper, connection, target):
    target.search_vector = func.to_tsvector('english', target.title + ' ' + target.artist_name)
    

# we need to create this placeholder track for unknown tracks, will have id 1 always
@listens_for(Track.__table__, 'after_create')    
def insert_unknown_track(target, connection, **kw):
    connection.execute(
        target.insert().values(
            key_track_shazam=-1, # thoses keys still have to be unique (for tracks that will not have one or either of those keys)
            key_track_spotify='-',
            key_track_apple='-',
            title='Unknown Track',
            artist_name='Unknown Artist',
            album=None,
            label=None,
            cover_arts=None,
            preview_uris=None,
            uri_apple=None,
            release_year=None,
            release_date=None,
            artist_popularity_spotify=None,
            nb_sets=0,
            nb_playlists=0,
            related_tracks_checked=False
        )
    )

@listens_for(Set.__table__, 'after_create')
def create_tsvector_trigger(target, connection, **kw):
    connection.execute(DDL("""
        CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE ON sets
        FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(title_tsv, 'pg_catalog.english', title);
    """))


def search_sets_by_title_and_author(search_query):
    search_vector = func.to_tsvector('english', search_query)
    results = db.session.query(Set).join(Channel).filter(
        Set.title_tsv.match(search_query),
        Channel.author.ilike(f"%{search_query}%")
    ).all()
    return results  

# search for playlists and tracks
def search_playlist(search_terms):
    query = db.session.query(Playlist).join(TrackPlaylist).join(Track).filter(
        search(Playlist.search_vector, 'search term') |
        search(Track.search_vector, 'search term')
    )
    results = query.all()
 
 