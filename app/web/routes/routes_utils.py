
from flask import jsonify, redirect, request, url_for
from config import Config
from flask_login import current_user

from web.controller import get_playlists_from_user
from web.lib.format import apple_has_track, apple_music_thumbnail, apple_track_url, get_cover_art, key_mode, km_number, sec_to_mm_ss, spotify_has_track, spotify_track_url, time_ago, youtube_thumbnail

def is_connected():
    return current_user.is_authenticated

def is_admin():    
    if not is_connected():
        return False
    
    #print( current_user.id, Config.ADMIN_UID)  # 3, 3
    return str(current_user.id) == str(Config.ADMIN_UID) # False
    

def get_user_id():
    if is_connected():
        return current_user.id
    return None

def redirect_if_not_connected():
    if not is_connected():
        return redirect(url_for('users.login', next=request.endpoint))
    
def jax_redirect_if_not_connected(next_url=None):
    if is_connected():
        return False
    
    redirect_url = url_for('users.login',next=next_url) 
    return jsonify({"redirect":redirect_url }), 401
  
  
  
   # All the small formating utils needed in the templates
tpl_utils = {
        'time_ago': time_ago,
        'sec_to_mm_ss': sec_to_mm_ss,
        'km_number': km_number,
        'key_mode': key_mode,
        'spotify_track_url': spotify_track_url,
        'apple_track_url': apple_track_url,
        'get_cover_art': get_cover_art,
        'spotify_has_track':spotify_has_track,
        'apple_has_track':apple_has_track,
        'user_playlists': get_playlists_from_user,
        'youtube_thumbnail': youtube_thumbnail,
        'apple_music_thumbnail': apple_music_thumbnail
        }
  