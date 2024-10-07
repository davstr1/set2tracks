from re import L, sub
import re
from flask import Blueprint, Config, redirect, render_template, request, url_for
from flask_login import current_user
from web.routes.routes_utils import tpl_utils

from lang import Lang
from web.controller import get_tracks



track_bp = Blueprint('track', __name__)


@track_bp.route('/explore/tracks')
def tracks():
    
    
    PER_PAGE = 30
    page = request.args.get('page', 1, type=int)
    search = request.args.get('s', '', type=str)
    order_by = request.args.get('order_by', 'recent', type=str)
    tracks,tracks_raw,results_count = get_tracks(search=search, page=page, per_page=PER_PAGE)
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
        return url_for('track.tracks', **params)

    pagination = {}
    if tracks_raw.has_prev:
        pagination['prev_url'] = get_pagination_url(page - 1)
    if tracks_raw.has_next:
        pagination['next_url'] = get_pagination_url(page + 1)
    
    is_paginated = tracks_raw.has_next or tracks_raw.has_prev
    
    return render_template('tracks.html', 
                           tracks=tracks,
                           results_count=results_count,
                           pagination=pagination,
                           is_paginated=is_paginated,
                           search=search,
                           tpl_utils=tpl_utils,
                           l=l,
                           page_name='explore',
                           subpage_name='tracks',)

