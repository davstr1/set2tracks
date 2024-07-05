
from datetime import datetime, timezone
import json
from math import log
import os
from pprint import pprint
import re
from venv import logger



from flask import g, jsonify, make_response, render_template,redirect,url_for,request,flash
from flask.cli import F
from flask_login import current_user, login_required

from web import bp
from flask_babel import lazy_gettext as _l

from web.controller import   add_track_to_playlist, add_track_to_playlist_last_used, change_playlist_title, create_playlist, create_playlist_from_set_tracks, create_spotify_playlist_and_add_tracks, delete_playlist, format_db_tracks_for_template,get_playable_sets, get_playlist_with_tracks, get_set_genres_by_occurrence, get_set_id_by_video_id, get_set_with_tracks, get_track_by_id, get_playlists_from_user, is_set_exists, queue_set, remove_track_from_playlist, update_playlist_positions_after_track_change_position

from web.lib.related_tracks import save_related_tracks
from web.lib.spotify import ensure_valid_token, get_client_auth_url, get_client_playlists, get_client_token
from web.lib.utils import calculate_and_sort_tempo_distribution, calculate_avg_properties, calculate_decade_distribution
from web.lib.youtube import  youtube_video_id_from_url, youtube_video_input_is_valid
from web.lib.format import apple_has_track, format_db_track_for_template, get_cover_art, spotify_has_track, time_ago,km_number,key_mode,spotify_track_url,apple_track_url

from dotenv import load_dotenv
import os

from web.model import Playlist, SetQueue
import logging
logger = logging.getLogger('root')
load_dotenv()

AUDIO_SEGMENTS_LENGTH = int(os.getenv('AUDIO_SEGMENTS_LENGTH'))



def is_connected():
    return current_user.is_authenticated

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
    print('next_url:',next_url)
    print('redirect_url:',redirect_url)
   
    return jsonify({"redirect":redirect_url }), 401


@bp.before_request
def before_request():
    
    # All the small formating utils needed in the templates
    g.utils = {
        'time_ago': time_ago,
        'km_number': km_number,
        'key_mode': key_mode,
        'spotify_track_url': spotify_track_url,
        'apple_track_url': apple_track_url,
        'get_cover_art': get_cover_art,
        'spotify_has_track':spotify_has_track,
        'apple_has_track':apple_has_track,
    }
    
    user_id = get_user_id()
    
    if user_id:
        g.user_playlists = get_playlists_from_user(user_id, order_by='title')




@bp.route('/')
def index():
    return render_template('index.html')
       
@bp.route('/dashboard')
def dashboard():
    if current_user.is_authenticated:
        next_page_cookie = request.cookies.get('next_page_after_login')
        if next_page_cookie:
            response = redirect(next_page_cookie)
            response.delete_cookie('next_page_after_login')
            return response
            
            
        return render_template('dashboard.html')
    
    return redirect(url_for('main.index'))



@bp.route('/add', methods=['GET', 'POST'])
def add():
    if not is_connected():
        return redirect(url_for('users.login', next=url_for('main.add')))
    if request.method == 'POST':
        youtube_url = request.form.get('youtube_url')
        if not youtube_url:
            flash('No YouTube URL provided. Please enter a URL.', 'error')
            return redirect(url_for('main.add'))
        if not youtube_video_input_is_valid(youtube_url):
            flash('Invalid YouTube URL. Please enter a valid URL.', 'error')
            return redirect(url_for('main.add'))
       
        
        # Process the YouTube URL as needed
        # Example of successful processing redirect or message
        #flash('URL received successfully.', 'success')
        video_id = youtube_video_id_from_url(youtube_url)
        return redirect(url_for('main.insert_set_route',video_id=video_id))
    return render_template('add.html',no_flash_top=True)


@bp.route('/insert_set/<video_id>', methods=['GET'])
def insert_set_route(video_id):
    
    if (is_set_exists(video_id)):
       return redirect(url_for('main.set',set_id=get_set_id_by_video_id(video_id))) 
    
    result = queue_set(video_id,get_user_id()) #insert_set(video_id)
   
   
    if isinstance(result, dict) and 'error' in result:
        flash(result['error'], 'error')
        return redirect(url_for('main.add'))

    if isinstance(result, SetQueue) and result.id:
        flash('Set added to the queue', 'success')
        return redirect(url_for('main.add'))
    
@bp.route('/set/<int:set_id>')
def set(set_id):
    set = get_set_with_tracks(set_id)
    
    
    if 'error' in set:
        return redirect(url_for('main.index'))
    

    
   
    #avg_properties = calculate_avg_properties(set['tracks'])
 
    # most_common_decades = calculate_decade_distribution(set['tracks'])
    # most_common_tempos = calculate_and_sort_tempo_distribution(set['tracks'])
    # pprint(avg_properties)
    # pprint('------')
    # print(most_common_decades)
    # print(most_common_tempos)
    #pprint(get_set_avg_characteristics(set_id))

    return render_template('set.html', set=set)





@bp.route('/sets')
def sets():    
    page = request.args.get('page', 1, type=int)
    sets_page = get_playable_sets(page=page, per_page=20)
    playlists_user = get_playlists_from_user(1)
    return render_template('sets.html', sets_page=sets_page)




@bp.route('/related_tracks/<int:track_id>')
def related_tracks(track_id):
    track = get_track_by_id(track_id)
    if not track:
        logger.error(f"Track with ID {track_id} does not exist.")
        return redirect(request.referrer or url_for('main.index'))
    
    if track.related_tracks and len(track.related_tracks) > 0:
        related_tracks =format_db_tracks_for_template(track.related_tracks)
        track_formated = format_db_track_for_template(track)
        return render_template('related_tracks.html',track=track_formated,tracks=related_tracks)
    else:
        logger.info('no related tracks')
        return redirect(request.referrer or url_for('main.index'))
        

@bp.route('/playlists')  
def my_playlists():
    user_id = get_user_id()
    playlists = []
    
    if user_id:
        playlists = get_playlists_from_user(user_id)
        
    return render_template('playlists.html',user_id=user_id,playlists=playlists)


@bp.route('/playlist/create', methods=['GET', 'POST'])
def playlist_create():
    if not is_connected():
        return redirect(url_for('users.login', next=url_for('main.playlist_create')))

    if request.method == 'POST':
        playlist_title = request.form.get('title').strip()

        # Validate the playlist name
        if not playlist_title:
            flash('Playlist name cannot be empty', 'error')
            return redirect(url_for('main.playlist_create'))
        
        if len(playlist_title) > 255:
            flash('Playlist name cannot be longer than 255 characters', 'error')
            return redirect(url_for('main.playlist_create'))
        
        user_id = get_user_id()

        # Check for duplicate playlist name for the user
        # existing_playlist = Playlist.query.filter_by(user_id=user_id, title=playlist_title).first()
        # if existing_playlist:
        #     flash('You already have a playlist with this name', 'error')
        #     return redirect(url_for('main.playlist_create'))

        new_playlist = create_playlist(user_id, playlist_title)

        if not new_playlist:
            flash('Failed to create playlist', 'error')
            return redirect(url_for('main.playlist_creat'))
        
        flash('Playlist created successfully', 'success')
        return redirect(url_for('main.my_playlists'))

    return render_template('playlist_create.html')

@bp.route('/playlist/<int:playlist_id>', methods=['GET', 'POST'])
def show_playlist(playlist_id):
    res = get_playlist_with_tracks(playlist_id)

    return render_template('playlist.html',playlist=res['playlist'],tracks=res['tracks'])



@bp.route('/playlist/<int:playlist_id>/edit', methods=['GET', 'POST'])
def playlist_edit(playlist_id):

    if request.method != 'POST':
        res = get_playlist_with_tracks(playlist_id)
        return render_template('playlist_edit.html',playlist=res['playlist'])
    
    else:
    
    
        try:
            
            data = request.form
        
            title_new = data.get('title_new').strip()
            title_old = data.get('title_old').strip()
            logger.info(f'changing playlist title from {title_old} to {title_new}')
            if title_new == title_old:
                raise ValueError('The new title is the same as the old one')



            response = change_playlist_title(playlist_id,title_new )
            
            if 'error' in response:
                logger.error(f'error in response {response["error"]}')
                raise Exception(response['error'], 'error')


            flash(response['message'], 'success')
            return redirect(url_for('main.my_playlists'))

        except Exception as e:
            logger.error(f'error in playlist edit {e}')
            flash(str(e), 'error')
            res = get_playlist_with_tracks(playlist_id)
            return render_template('playlist_edit.html',playlist=res['playlist'])
    
    
@bp.route('/playlist/<int:playlist_id>/delete')
def playlist_delete(playlist_id):
    try:
        message = delete_playlist(playlist_id)
        if 'error' in message:
            flash(message['error'], 'error')
            return redirect(url_for('main.playlist_edit', playlist_id=playlist_id))
        
        flash('Playlist deleted successfully', 'success')
        return redirect(url_for('main.my_playlists'))
    except Exception as e:
        flash(str(e), 'error')
    return redirect(url_for('main.playlist_edit', playlist_id=playlist_id))
    
       
    
    
@bp.route('/spotify_auth')
def spotify_auth():
    auth_url = get_client_auth_url()
    next_page = request.args.get('next')
    
    response = make_response(redirect(auth_url))
    if next_page:
        response.set_cookie('next_page_after_spofify_auth', next_page, max_age=600, httponly=False, samesite='Lax', path='/')
    
    return response


@bp.route('/spotify_callback')
def callback():
    token_spotify = get_client_token()
    logger.info(token_spotify)
    next_page_cookie = request.cookies.get('next_page_after_spofify_auth')
    if next_page_cookie:
            response = redirect(next_page_cookie)
            response.delete_cookie('next_page_after_spofify_auth')
            return response
    
    # No cookie, no clue bro    
    return redirect(url_for('main.index'))

@bp.route('/spotify_playlists')
def spotify_playlists():
    playlists = get_client_playlists()
    
    pprint(playlists)
    return 'ok'




@bp.route('/playlist_to_spotify/<int:playlist_id>')
def playlist_to_spotify(playlist_id):
    
    try:
        # connect to spotify
        token_spotify = ensure_valid_token()
        
        # Not connected to Spotify
        if token_spotify is None :
            return redirect(url_for('main.spotify_auth', next=url_for('main.playlist_to_spotify',playlist_id=playlist_id)))
        
        
        res = get_playlist_with_tracks(playlist_id)
        playlist = res['playlist']
        tracks = res['tracks']
        
        res = create_spotify_playlist_and_add_tracks(playlist.get('title'), tracks)
        

        return jsonify(res)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

### JAx routes

@bp.route('/jax/update_position', methods=['POST'])
def update_position():
    data = request.json
    
    if not all(k in data for k in ("playlist_id", "track_id", "new_position")):
        return jsonify({"error": "Missing required parameters"}), 400
    
    playlist_id = data['playlist_id']
    track_id = data['track_id']
    new_position = data['new_position']
    
    try:
        update_playlist_positions_after_track_change_position(playlist_id, track_id, new_position)
        return jsonify({"message": "Track position updated successfully"}), 200
    except Exception as e:
        
        return jsonify({"error": str(e)}), 500
    
    
@bp.route('/jax/add_track_to_playlist', methods=['POST'])
def jax_add_track_to_playlist():
    

    data = request.json
    playlist_id = data['playlist_id']
    track_id = data['track_id']
    
    try:
        response = add_track_to_playlist(playlist_id, track_id)
        if 'error' in response:
            return jsonify({"error": response['error']}), 409
        
        return jsonify({"message": response['message']}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@bp.route('/jax/add_track_to_playlist_last_used', methods=['POST'])
def jax_add_track_to_playlist_last_used():
    
   
    
    data = request.json 
    print(data)
    track_id = data['track_id']
    caller_url = data['caller_url'] if 'caller_url' in data else None
    
    user_id = get_user_id()
    
    if not user_id:
        return jax_redirect_if_not_connected(next_url=caller_url)
    
    try:
        response = add_track_to_playlist_last_used(track_id, user_id)
        if 'error' in response:
            logger.error('error in response',response['error'])
            return jsonify({"error": response['error']}), 409
        
        return jsonify({"message": response['message']}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/jax/remove_track_from_playlist', methods=['POST'])
def jax_remove_track_from_playlist():
    data = request.json
    playlist_id = data['playlist_id']
    track_id = data['track_id']
    
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "User not connected"}), 401
    
    try:
        response = remove_track_from_playlist(playlist_id,track_id, user_id)
        if 'error' in response:
            logger.error(f"error in removing track response : {response['error']}")
            return jsonify({"error": response['error']}), 409
        
        return jsonify({"message": response['message']}), 200
    except Exception as e:
        logger.error(f' Unknown error in removing track : {str(e)}')
        return jsonify({"error": str(e)}), 500
    
    
@bp.route('/jax/create_playlist_from_set_tracks', methods=['POST'])
def jax_create_playlist_from_set_tracks():
    data = request.json
    set_id = data['set_id']
    
    user_id = get_user_id()
    if not user_id:
        set_uri = url_for('main.set',set_id=set_id)
        redirect_uri = url_for('users.login', next=set_uri)
        return jsonify({"error": "User not connected",'redirect':redirect_uri}), 401
    
    try:
        response = create_playlist_from_set_tracks(set_id, user_id)
          
        if 'error' in response:
            return jsonify({"error": response['error']}), 409
        
        return jsonify({"message": response['message']}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@bp.route('/jax/check_save_related_tracks/<int:track_id>', methods=['GET'])
def jax_check_save_related_tracks(track_id):
    
    track = get_track_by_id(track_id)
    if not track:
        return jsonify({'error':f"Track with ID {track_id} does not exist."}), 404
    
    if track.related_tracks_checked and len(track.related_tracks) > 0:
        return jsonify({'message': f"Related tracks already saved for track ID {track_id}"}), 200
    
    if track.related_tracks_checked and len(track.related_tracks) == 0:
        return jsonify({'error': f"No related tracks found for track ID {track_id}"}), 500
    
    try:    
        ret = save_related_tracks(track)
        
        if 'error' in ret:
            return jsonify({'error':f"Error saving related tracks: {ret['error']}"}), 409
        return jsonify({'message': f"Related tracks saved for track ID {track_id}"}),200
    except Exception as e:
        return jsonify({'error':f"Error saving related tracks: {e}"}), 500
    


