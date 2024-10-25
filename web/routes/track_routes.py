from re import L, sub
import re
from flask import Blueprint, Config, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import asc
from web.routes.routes_utils import get_user_id, tpl_utils

from lang import Lang
from web.controller import get_playlists_from_user, get_tracks, get_tracks_min_maxes



track_bp = Blueprint('track', __name__)


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
    
    instrumental_min = 100 - vocal_max if vocal_max is not None else None
    instrumental_max = 100 - vocal_min if vocal_min is not None else None
    
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
        order_by=order_by,
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
        return url_for('track.tracks', **params)

    pagination = {}
    if tracks_raw.has_prev:
        pagination['prev_url'] = get_pagination_url(page - 1)
    if tracks_raw.has_next:
        pagination['next_url'] = get_pagination_url(page + 1)
    
    is_paginated = tracks_raw.has_next or tracks_raw.has_prev
    
    
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
        
    vocal_min = 100 - instrumental_max if instrumental_max is not None else None
    vocal_max = 100 - instrumental_min if instrumental_min is not None else None
    vocal_min_default = 100 - min_maxes['instrumental_max']
    vocal_max_default = 100 - min_maxes['instrumental_min']
    print(min_maxes)
    
    user_id = get_user_id()
    
    if user_id:
        user_playlists = get_playlists_from_user(user_id, order_by='az',page=1,per_page=100)
    else:
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
                            order_by=order_by,
                            asc=asc,
                           tpl_utils=tpl_utils,
                           l=l,
                           current_url=current_url,
                           page_name='explore',
                           subpage_name='tracks',)

