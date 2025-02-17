from web.model import Track, Genre
from sqlalchemy import and_, func, or_
from web.lib.format import format_db_track_for_template, format_db_tracks_for_template

def get_tracks_min_maxes():
    return {}
    # Get the minimum and maximum values for release year and BPM from every track in the database, excluding zeroes and nulls.
    # year_min = Track.query.with_entities(func.min(Track.release_year)).filter(Track.release_year.isnot(None), Track.release_year != 0).scalar()
    # year_max = Track.query.with_entities(func.max(Track.release_year)).filter(Track.release_year.isnot(None), Track.release_year != 0).scalar()
    # bpm_min = Track.query.with_entities(func.min(Track.tempo)).filter(Track.tempo.isnot(None), Track.tempo != 0).scalar()
    # bpm_max = Track.query.with_entities(func.max(Track.tempo)).filter(Track.tempo.isnot(None), Track.tempo != 0).scalar()
    # instrumental_min = Track.query.with_entities(func.min(Track.instrumentalness)).filter(Track.instrumentalness.isnot(None), Track.instrumentalness != 0).scalar()
    # instrumental_max = Track.query.with_entities(func.max(Track.instrumentalness)).filter(Track.instrumentalness.isnot(None), Track.instrumentalness != 0).scalar()
    # acoustic_min = Track.query.with_entities(func.min(Track.acousticness)).filter(Track.acousticness.isnot(None), Track.acousticness != 0).scalar()
    # acoustic_max = Track.query.with_entities(func.max(Track.acousticness)).filter(Track.acousticness.isnot(None), Track.acousticness != 0).scalar()
    # speech_min = Track.query.with_entities(func.min(Track.speechiness)).filter(Track.speechiness.isnot(None), Track.speechiness != 0).scalar()
    # speech_max = Track.query.with_entities(func.max(Track.speechiness)).filter(Track.speechiness.isnot(None), Track.speechiness != 0).scalar()
    # danceability_min = Track.query.with_entities(func.min(Track.danceability)).filter(Track.danceability.isnot(None), Track.danceability != 0).scalar()
    # danceability_max = Track.query.with_entities(func.max(Track.danceability)).filter(Track.danceability.isnot(None), Track.danceability != 0).scalar()
    # energy_min = Track.query.with_entities(func.min(Track.energy)).filter(Track.energy.isnot(None), Track.energy != 0).scalar()
    # energy_max = Track.query.with_entities(func.max(Track.energy)).filter(Track.energy.isnot(None), Track.energy != 0).scalar()
    # loudness_min = Track.query.with_entities(func.min(Track.loudness)).filter(Track.loudness.isnot(None), Track.loudness != 0).scalar()
    # loudness_max = Track.query.with_entities(func.max(Track.loudness)).filter(Track.loudness.isnot(None), Track.loudness != 0).scalar()
    # valence_min = Track.query.with_entities(func.min(Track.valence)).filter(Track.valence.isnot(None), Track.valence != 0).scalar()
    # valence_max = Track.query.with_entities(func.max(Track.valence)).filter(Track.valence.isnot(None), Track.valence != 0).scalar()
    # return {
    #     'year_min': year_min, 'year_max': year_max, 
    #     'bpm_min': bpm_min, 'bpm_max': bpm_max, 
    #     'instrumental_min': instrumental_min, 'instrumental_max': instrumental_max,
    #     'acoustic_min': acoustic_min, 'acoustic_max': acoustic_max,
    #     'speech_min': speech_min, 'speech_max': speech_max,
    #     'danceability_min': danceability_min, 'danceability_max': danceability_max,
    #     'energy_min': energy_min, 'energy_max': energy_max,
    #     'loudness_min': loudness_min, 'loudness_max': loudness_max,
    #     'valence_min': valence_min, 'valence_max': valence_max
    #     }
    
    
def get_tracks(
        page=1,
        per_page=20,
        search=None,
        # bpm_min=None,bpm_max=None,
        # year_min=None,year_max=None,
        # instrumental_min=None,instrumental_max=None,
        # acoustic_min=None,acoustic_max=None,
        # speech_min=None,speech_max=None,
        # danceability_min=None,danceability_max=None,
        # energy_min=None,energy_max=None,
        # loudness_min=None,loudness_max=None,
        # valence_min=None,valence_max=None,
        order_by=None,asc=None,
        genre=None,
        label=None,
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
        
    if label:
        query = query.filter(Track.label.ilike(f"%{label}%"))
        
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

        
    
    # if bpm_min:
    #     query = query.filter(Track.tempo >= bpm_min)
    # if bpm_max:
    #     query = query.filter(Track.tempo <= bpm_max)    
    # if year_min:
    #     query = query.filter(Track.release_year >= year_min)
    # if year_max:
    #     query = query.filter(Track.release_year <= year_max)
    # if instrumental_min:
    #     query = query.filter(Track.instrumentalness >= instrumental_min)
    # if instrumental_max:
    #     query = query.filter(Track.instrumentalness <= instrumental_max)
    # if acoustic_min:
    #     query = query.filter(Track.acousticness >= acoustic_min)
    # if acoustic_max:
    #     query = query.filter(Track.acousticness <= acoustic_max)
    # if speech_min:
    #     query = query.filter(Track.speechiness >= speech_min)
    # if speech_max:
    #     query = query.filter(Track.speechiness <= speech_max)
    # if danceability_min:
    #     query = query.filter(Track.danceability >= danceability_min)
    # if danceability_max:
    #     query = query.filter(Track.danceability <= danceability_max)
    # if energy_min:
    #     query = query.filter(Track.energy >= energy_min)
    # if energy_max:
    #     query = query.filter(Track.energy <= energy_max)
    # if loudness_min:
    #     query = query.filter(Track.loudness >= loudness_min)
    # if loudness_max:
    #     query = query.filter(Track.loudness <= loudness_max)
    # if valence_min:
    #     query = query.filter(Track.valence >= valence_min)

        
    count = query.count()    
    
    # year_min = Track.query.with_entities(func.min(Track.release_year)).scalar()
    # year_max = Track.query.with_entities(func.max(Track.release_year)).scalar()
        
    ret = query.paginate(page=page, per_page=per_page, error_out=False)
    tracks_for_template  = format_db_tracks_for_template(ret.items)
    return tracks_for_template,ret,count    



def get_track_by_id(track_id,format_for_template=True):
    track = Track.query.get(track_id)
    if not track :
        return None
    if format_for_template:
        return format_db_track_for_template(track)
    return track



    
def tracks_to_tracks_ids(tracks):
    return [track['id'] for track in tracks]

def get_track_by_shazam_key(key_track_shazam):
    return Track.query.filter_by(key_track_shazam=key_track_shazam).first()   
 