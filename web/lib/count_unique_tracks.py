def count_unique_tracks(tracks_json):
 
    tracks_unique = {}
    try:
        for track in tracks_json:
            if track and 'title' in track and 'artist_name' in track and track['title'] and track['artist_name']:
                key = track['title'] + track['artist_name']
                if key not in tracks_unique:
                    tracks_unique[key] = track
    except Exception as e:
        return 0
      
    return len(tracks_unique)
        
    