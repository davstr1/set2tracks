from unittest import result
from flask import Blueprint, flash, make_response, redirect, render_template, request, url_for
from web.lib.format import apple_track_url, spotify_track_url
from web.lib.utils import get_compatible_keys
from web.routes.routes_utils import get_user_id, is_connected, tpl_utils

from lang import Lang
from web.controller.track import get_track_by_id, get_tracks_min_maxes,get_tracks


track_bp = Blueprint('track', __name__)


@track_bp.route('/track/<int:track_id>/<string:music_service>')
def track_link(track_id, music_service):
    error_redirect = url_for('set.sets')
    # Music service should be either 'spotify' or 'apple'
    track = get_track_by_id(track_id=track_id)

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

    genre = request.args.get('genre', '', type=str)
    label = request.args.get('label', '', type=str)
    
    
    order_by = request.args.get('order_by', '', type=str)
    asc = request.args.get('asc', None, type=str)
    

    tracks,tracks_raw,results_count = get_tracks(
        search=search, 
        page=page, 
        per_page=PER_PAGE, 
        order_by=order_by,
        genre=genre,
        label=label,
        asc=asc
        )
    
    
    results_count_str = str(results_count)
    if label:
        page_title = results_count_str + ' tracks from label ' + label + ' – Discover,Prelisten & Export'
        page_meta = f'Explore {label} tracks, prelisten instantly, find similar tracks, and export your favorites to Spotify & Apple Music.'
    elif genre:
        page_title = results_count_str + ' ' + genre + ' tracks – For DJs & Music Lovers'
        page_meta = f'Dive into {genre} music! Prelisten, find related tracks & labels, and export your playlists to Spotify & Apple Music.'
    else:
        page_title = results_count_str + ' tracks on ' + Lang.APP_NAME + ' – DJ’s Music Discovery Tool'
        page_meta = f'Discover fresh tracks, explore genres & labels, prelisten, and export directly to Spotify & Apple Music. Free for DJs & music lovers!'
  
    l = {
        'page_title' : page_title,
        'page_description' : page_meta,
    }
    
    def get_pagination_url(page):
        params = {}
        if search:
            params['s'] = search
        if order_by != 'recent':
            params['order_by'] = order_by
        if page != 1:
            params['page'] = page

        if genre:
            params['genre'] = genre
            
        return url_for('track.tracks', **params)

    pagination = {}
    if tracks_raw.has_prev:
        pagination['prev_url'] = get_pagination_url(page - 1)
    if tracks_raw.has_next:
        pagination['next_url'] = get_pagination_url(page + 1)
    
    is_paginated = tracks_raw.has_next or tracks_raw.has_prev
    


    
    user_id = get_user_id()
    
    user_playlists = []
        
    current_url = request.url

    return render_template('tracks.html', 
                           tracks=tracks,
                           results_count=results_count,
                           pagination=pagination,
                           is_paginated=is_paginated,
                           search=search,
                           user_playlists=user_playlists,
             
                            genre=genre,
                            label=label,
                            order_by=order_by,
                            asc=asc,
                           tpl_utils=tpl_utils,
                           l=l,
                           current_url=current_url,
                           page_name='explore',
                           subpage_name='tracks',)

