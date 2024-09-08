from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user

from web.controller import add_track_to_playlist, add_track_to_playlist_last_used, change_playlist_title, create_playlist, create_playlist_from_set_tracks, create_spotify_playlist_and_add_tracks, delete_playlist, get_playlist_with_tracks, get_playlists_from_user, remove_track_from_playlist, update_playlist_positions_after_track_change_position
from web.lib.spotify import ensure_valid_token
from web.routes.routes_utils import tpl_utils,get_user_id, is_connected, jax_redirect_if_not_connected
from web.logger import logger



admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/set/hide/<int:set_id>', methods=['GET'])  
def set_hide(set_id):
    # admin check
    # do the action
        
    return render_template(url_for('set',set_id=set_id))


@admin_bp.route('/admin/channel/hide/<int:channel_id>', methods=['GET'])  
def channel_hide(channel_id):
    # admin check
    # do the action
    
    return 1
        
    #return render_template(url_for('set',set_id=set_id))
