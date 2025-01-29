from flask import Blueprint, flash, make_response, redirect, render_template, request, url_for
from web.lib.format import apple_track_url, spotify_track_url
from web.lib.utils import get_compatible_keys
from web.routes.routes_utils import get_user_id, is_connected, tpl_utils

from lang import Lang
from web.controller import get_playlists_from_user, get_track_by_id, get_tracks, get_tracks_min_maxes



track_bp = Blueprint('track', __name__)


@track_bp.route('/track/<int:track_id>/<string:music_service>')
def track_link(track_id, music_service):
    error_redirect = url_for('set.sets')
    # Music service should be either 'spotify' or 'apple'
    track = get_track_by_id(track_id=track_id)
    print(track)
    if not track:
        flash('Track not found', 'error')
        return redirect(error_redirect)
    
    # Check if the user is authenticated
    if not is_connected():
        response = make_response(redirect(url_for('users.login', next=request.referrer)))
        #response.set_cookie('next_page_track_link', url_for('track.track_link',track_id=track_id,music_service=music_service), max_age=600, httponly=False, samesite='Lax', path='/')
        return response

    # Generate the URL for the specified music service
    if music_service.lower() == 'spotify':
        url = spotify_track_url(track)
    elif music_service.lower() == 'apple':
        url = apple_track_url(track)
    else:
        flash('Invalid music service', 'error')
        return redirect(error_redirect)
    
    # Redirect the user to the generated URL
    return redirect(url)


@track_bp.route('/explore/tracks/compatible/<int:track_id>')
def compatible_tracks(track_id):
    track = get_track_by_id(track_id=track_id)
    if not track:
        flash('Track not found', 'error')
        return redirect(url_for('track.tracks'))
    print(track['tempo'], track['key'], track['mode'])
    if not track['tempo'] or not track['key'] or track['mode'] is None:
        flash('Track has no key or tempo specified', 'error')
        return redirect(url_for('track.tracks'))
    
    tempo = track['tempo']
    key = track['key'] # 0-11
    mode = track['mode'] # 0,1. 
    
    # must be a comma separated string of the compatible keys
    # for example : "A1,A2,A3,B2"
    keys_compatible = get_compatible_keys(key, mode)
    
    
    return redirect(url_for('track.tracks', keys=keys_compatible, bpm_min=tempo-5, bpm_max=tempo+5))
    

@track_bp.route('/explore/tracks')
def tracks():
    
    
    
    PER_PAGE = 30
    page = request.args.get('page', 1, type=int)
    search = request.args.get('s', '', type=str)
    year_min = request.args.get('year_min', None, type=int)
    year_max = request.args.get('year_max', None, type=int)
    bpm_min = request.args.get('bpm_min', None, type=int)
    bpm_max = request.args.get('bpm_max', None, type=int)
    vocal_min = request.args.get('vocal_min', None, type=int)
    vocal_max = request.args.get('vocal_max', None, type=int)
    acoustic_min = request.args.get('acoustic_min', None, type=int)
    acoustic_max = request.args.get('acoustic_max', None, type=int)
    speech_min = request.args.get('speech_min', None, type=int)
    speech_max = request.args.get('speech_max', None, type=int)
    danceability_min = request.args.get('danceability_min', None, type=int)
    danceability_max = request.args.get('danceability_max', None, type=int)
    energy_min = request.args.get('energy_min', None, type=int)
    energy_max = request.args.get('energy_max', None, type=int)
    loudness_min = request.args.get('loudness_min', None, type=int)
    loudness_max = request.args.get('loudness_max', None, type=int)
    valence_min = request.args.get('valence_min', None, type=int)
    valence_max = request.args.get('valence_max', None, type=int)
    
    instrumental_min = 100 - vocal_max if vocal_max is not None else None
    instrumental_max = 100 - vocal_min if vocal_min is not None else None
    
    keys = request.args.get('keys', '', type=str)
    genre = request.args.get('genre', '', type=str)
    
    
    order_by = request.args.get('order_by', '', type=str)
    asc = request.args.get('asc', None, type=str)
    
    min_maxes = get_tracks_min_maxes()
    if year_min == min_maxes['year_min']:
        year_min = None
    if year_max == min_maxes['year_max']:
        year_max = None
    if bpm_min == min_maxes['bpm_min']:
        bpm_min = None
    if bpm_max == min_maxes['bpm_max']:
        bpm_max = None
    if instrumental_min == min_maxes['instrumental_min']:
        instrumental_min = None
    if instrumental_max == min_maxes['instrumental_max']:
        instrumental_max = None
    if acoustic_min == min_maxes['acoustic_min']:
        acoustic_min = None
    if acoustic_max == min_maxes['acoustic_max']:
        acoustic_max = None
    if speech_min == min_maxes['speech_min']:
        speech_min = None
    if speech_max == min_maxes['speech_max']:
        speech_max = None
    if danceability_min == min_maxes['danceability_min']:
        danceability_min = None
    if danceability_max == min_maxes['danceability_max']:
        danceability_max = None
    if energy_min == min_maxes['energy_min']:
        energy_min = None
    if energy_max == min_maxes['energy_max']:
        energy_max = None
    if loudness_min == min_maxes['loudness_min']:
        loudness_min = None
    if loudness_max == min_maxes['loudness_max']:
        loudness_max = None
    if valence_min == min_maxes['valence_min']:
        valence_min = None
    if valence_max == min_maxes['valence_max']:
        valence_max = None
    
    
    tracks,tracks_raw,results_count = get_tracks(
        search=search, 
        page=page, 
        per_page=PER_PAGE, 
        year_min=year_min, 
        year_max=year_max,
        bpm_max=bpm_max,
        bpm_min=bpm_min,
        instrumental_min=instrumental_min,
        instrumental_max=instrumental_max,
        acoustic_min=acoustic_min,
        acoustic_max=acoustic_max,
        danceability_min=danceability_min,
        danceability_max=danceability_max,
        energy_min=energy_min,
        energy_max=energy_max,
        loudness_min=loudness_min,
        loudness_max=loudness_max,
        valence_min=valence_min,
        valence_max=valence_max,
        speech_min=speech_min,
        speech_max=speech_max,
        order_by=order_by,
        keys=keys,
        genre=genre,
        asc=asc
        )
    l = {
        'page_title' : 'Top 1000 Tracks - ' + Lang.APP_NAME
    }
    
    def get_pagination_url(page):
        params = {}
        if search:
            params['s'] = search
        if order_by != 'recent':
            params['order_by'] = order_by
        if page != 1:
            params['page'] = page
        if year_min is not None:
            params['year_min'] = year_min
        if year_max is not None:
            params['year_max'] = year_max
        if bpm_min is not None:
            params['bpm_min'] = bpm_min
        if bpm_max is not None:
            params['bpm_max'] = bpm_max
        if instrumental_min is not None:
            params['instrumental_min'] = instrumental_min
        if instrumental_max is not None:
            params['instrumental_max'] = instrumental_max
        if acoustic_min is not None:
            params['acoustic_min'] = acoustic_min
        if acoustic_max is not None:
            params['acoustic_max'] = acoustic_max
        if speech_min is not None:
            params['speech_min'] = speech_min
        if speech_max is not None:
            params['speech_max'] = speech_max
        if danceability_min is not None:
            params['danceability_min'] = danceability_min
        if danceability_max is not None:
            params['danceability_max'] = danceability_max
        if energy_min is not None:
            params['energy_min'] = energy_min
        if energy_max is not None:
            params['energy_max'] = energy_max
        if loudness_min is not None:
            params['loudness_min'] = loudness_min
        if loudness_max is not None:
            params['loudness_max'] = loudness_max
        if valence_min is not None:
            params['valence_min'] = valence_min
        if valence_max is not None:
            params['valence_max'] = valence_max
        if keys:
            params['keys'] = keys
        if genre:
            params['genre'] = genre
            
        return url_for('track.tracks', **params)

    pagination = {}
    if tracks_raw.has_prev:
        pagination['prev_url'] = get_pagination_url(page - 1)
    if tracks_raw.has_next:
        pagination['next_url'] = get_pagination_url(page + 1)
    
    is_paginated = tracks_raw.has_next or tracks_raw.has_prev
    
    

        
    vocal_min = 100 - instrumental_max if instrumental_max is not None else None
    vocal_max = 100 - instrumental_min if instrumental_min is not None else None
    vocal_min_default = 100 - min_maxes['instrumental_max']
    vocal_max_default = 100 - min_maxes['instrumental_min']

    
    user_id = get_user_id()
    
    # if user_id:
    #     user_playlists = get_playlists_from_user(user_id, order_by='edit_date',page=1,per_page=100)
    # else:
    #     user_playlists = []
    # Ditch this for now
    user_playlists = []
        
    current_url = request.url

    return render_template('tracks.html', 
                           tracks=tracks,
                           results_count=results_count,
                           pagination=pagination,
                           is_paginated=is_paginated,
                           search=search,
                           user_playlists=user_playlists,
                           year_min=year_min,
                            year_max=year_max,
                            year_min_default=min_maxes['year_min'],
                            year_max_default=min_maxes['year_max'],
                            bpm_min=bpm_min,
                            bpm_max=bpm_max,
                            bpm_min_default=min_maxes['bpm_min'],
                            bpm_max_default=min_maxes['bpm_max'],
                            vocal_min=vocal_min,
                            vocal_max=vocal_max,
                            vocal_min_default=vocal_min_default,
                            vocal_max_default=vocal_max_default,
                            acoustic_min=acoustic_min,
                            acoustic_max=acoustic_max,
                            acoustic_min_default=min_maxes['acoustic_min'],
                            acoustic_max_default=min_maxes['acoustic_max'],
                            speech_min=speech_min,
                            speech_max=speech_max,
                            speech_min_default=min_maxes['speech_min'],
                            speech_max_default=min_maxes['speech_max'],
                            danceability_min=danceability_min,
                            danceability_max=danceability_max,
                            danceability_min_default=min_maxes['danceability_min'],
                            danceability_max_default=min_maxes['danceability_max'],
                            energy_min=energy_min,
                            energy_max=energy_max,
                            energy_min_default=min_maxes['energy_min'],
                            energy_max_default=min_maxes['energy_max'],
                            loudness_min=loudness_min,
                            loudness_max=loudness_max,
                            loudness_min_default=min_maxes['loudness_min'],
                            loudness_max_default=min_maxes['loudness_max'],
                            valence_min=valence_min,
                            valence_max=valence_max,
                            valence_min_default=min_maxes['valence_min'],
                            valence_max_default=min_maxes['valence_max'],
                            keys=keys,
                            genre=genre,
                            order_by=order_by,
                            asc=asc,
                           tpl_utils=tpl_utils,
                           l=l,
                           current_url=current_url,
                           page_name='explore',
                           subpage_name='tracks',)

