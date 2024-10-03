from re import L, sub
from flask import Blueprint, Config, redirect, render_template, request, url_for
from flask_login import current_user
from web.routes.routes_utils import tpl_utils

from lang import Lang
from web.controller import get_tracks



track_bp = Blueprint('track', __name__)


@track_bp.route('/explore/tracks')
def tracks():
    
    tracks = get_tracks()
    l = {
        'page_title' : 'Top 1000 Tracks - ' + Lang.APP_NAME
    }
    return render_template('tracks.html', 
                           tracks=tracks,
                           tpl_utils=tpl_utils,
                           l=l,
                           page_name='explore',
                           subpage_name='tracks',)

