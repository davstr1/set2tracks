from flask import Blueprint, make_response, redirect, render_template, request, url_for
from flask_login import current_user

from web.lib.spotify import get_client_auth_url, get_client_playlists, get_client_token
from web.logger import logger

spotify_bp = Blueprint('spotify', __name__)


@spotify_bp.route('/spotify_auth')
def spotify_auth():
    auth_url = get_client_auth_url()
    next_page = request.args.get('next')
    
    response = make_response(redirect(auth_url))
    if next_page:
        response.set_cookie('next_page_after_spofify_auth', next_page, max_age=600, httponly=False, samesite='Lax', path='/')
    
    return response


@spotify_bp.route('/spotify_callback')
def callback():
    token_spotify = get_client_token()
    logger.info(token_spotify)
    next_page_cookie = request.cookies.get('next_page_after_spofify_auth')
    if next_page_cookie:
            response = redirect(next_page_cookie)
            response.delete_cookie('next_page_after_spofify_auth')
            return response
    
    # No cookie, no clue bro    
    return redirect(url_for('basic.index'))

@spotify_bp.route('/spotify_playlists')
def spotify_playlists():
    playlists = get_client_playlists()
    
    
    return 'ok'
