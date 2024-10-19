from re import L, sub
import re
from flask import Blueprint, Config, redirect, render_template, request, url_for
from flask_login import current_user
from web.routes.routes_utils import tpl_utils

from lang import Lang
from web.controller import get_tracks, get_tracks_min_maxes



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
    instrumental_min = request.args.get('instrumental_min', None, type=int)
    instrumental_max = request.args.get('instrumental_max', None, type=int)
    order_by = request.args.get('order_by', 'recent', type=str)
    
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
    
    
    tracks,tracks_raw,results_count = get_tracks(search=search, page=page, per_page=PER_PAGE, year_min=year_min, year_max=year_max,bpm_max=bpm_max,bpm_min=bpm_min,instrumental_min=instrumental_min,instrumental_max=instrumental_max, order=order_by)
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
    
    
    return render_template('tracks.html', 
                           tracks=tracks,
                           results_count=results_count,
                           pagination=pagination,
                           is_paginated=is_paginated,
                           search=search,
                           year_min=year_min,
                            year_max=year_max,
                            year_min_default=min_maxes['year_min'],
                            year_max_default=min_maxes['year_max'],
                            bpm_min=bpm_min,
                            bpm_max=bpm_max,
                            bpm_min_default=min_maxes['bpm_min'],
                            bpm_max_default=min_maxes['bpm_max'],
                            instrumental_min=instrumental_min,
                            instrumental_max=instrumental_max,
                            instrumental_min_default=min_maxes['instrumental_min'],
                            instrumental_max_default=min_maxes['instrumental_max'],
                           tpl_utils=tpl_utils,
                           l=l,
                           page_name='explore',
                           subpage_name='tracks',)

