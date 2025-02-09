
def get_track_by_shazam_key(key_track_shazam):
    return Track.query.filter_by(key_track_shazam=key_track_shazam).first()   

     
# Was in double
def get_track_by_id(id):
    return Track.query.filter_by(id=id).first()   


# Not currently in use

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