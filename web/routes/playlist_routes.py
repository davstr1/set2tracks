

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user



from lang import Lang
from web.controller import add_track_to_playlist, add_track_to_playlist_last_used, change_playlist_title, create_apple_playlist_and_add_tracks, create_playlist, create_playlist_from_set_tracks, create_spotify_playlist_and_add_tracks, delete_playlist, get_apple_music_dev_token, get_apple_music_user_token, get_playlist_with_tracks, get_playlists_from_user,  remove_track_from_playlist, set_apple_music_user_token, update_playlist_edit_date, update_playlist_positions_after_track_change_position ,add_all_tracks_from_set_to_playlist

from web.lib.spotify import add_tracks_to_spotify_playlist, ensure_valid_token, get_spotify_playlist_tracks_ids
from web.routes.routes_utils import tpl_utils,get_user_id, is_connected, jax_redirect_if_not_connected
from web.logger import logger



playlist_bp = Blueprint('playlist', __name__)


@playlist_bp.route('/playlists')  
def my_playlists():
    if not is_connected():
        return redirect(url_for('users.login', next=url_for('playlist.my_playlists')))
    
    user_id = get_user_id()
    playlists = []
    

    playlists = get_playlists_from_user(user_id)
        
    l = {
        'page_title': 'My Playlists' + ' - ' + Lang.APP_NAME, 
    }
        
    return render_template('playlists.html',user_id=user_id,playlists=playlists,tpl_utils=tpl_utils,page_name='my_playlists',l=l)


@playlist_bp.route('/playlist/create', methods=['GET', 'POST'])
def playlist_create():
    if not is_connected():
        return redirect(url_for('users.login', next=url_for('playlist.playlist_create', next=request.args.get('next'))))

    if request.method == 'POST':
        playlist_title = request.form.get('title').strip()
        next = request.form.get('next') or ''
        
        #return f'helllo {next}'

        # Validate the playlist name
        if not playlist_title:
            flash('Playlist name cannot be empty', 'error')
            return redirect(url_for('playlist.playlist_create', next=next))
        
        if len(playlist_title) > 255:
            flash('Playlist name cannot be longer than 255 characters', 'error')
            return redirect(url_for('playlist.playlist_create', next=next))
        
        user_id = get_user_id()
        new_playlist = create_playlist(user_id, playlist_title)

        if not new_playlist:
            flash('Failed to create playlist', 'error')
            return redirect(url_for('playlist.playlist_create', next=next))
        
        flash('Playlist created successfully', 'success')
        

        return redirect(next) if len(next) else redirect(url_for('playlist.my_playlists'))
    
    next = request.args.get('next') or ''
    
    l = {
        'page_title': 'Create a Playlist' + ' - ' + Lang.APP_NAME, 
    }
    
    return render_template('playlist_create.html', next=next, l=l)


@playlist_bp.route('/playlist/<int:playlist_id>', methods=['GET', 'POST'])
def show_playlist(playlist_id):
    res = get_playlist_with_tracks(playlist_id)
    
    playlist_author_id = res['playlist'].get('user_id')
    user_id = get_user_id()
    
    if playlist_author_id == user_id:
        # make this playlist the last used playlist
        update_playlist_edit_date(playlist_id)

    
    current_url = request.url
   
    
    if user_id:
        user_playlists = get_playlists_from_user(user_id, order_by='title')
    else:
        user_playlists = []
        
    l = {
        'page_title': res['playlist'].get('title') + ' - ' 'playlist' + ' ' + Lang.APP_NAME, 
    }

    return render_template('playlist.html',playlist=res['playlist'],tracks=res['tracks'],tpl_utils=tpl_utils,user_playlists=user_playlists,current_url=current_url,l=l)



@playlist_bp.route('/playlist/<int:playlist_id>/edit', methods=['GET', 'POST'])
def playlist_edit(playlist_id):
    if not is_connected():
        return redirect(url_for('users.login', next=url_for('playlist.playlist_edit', playlist_id=playlist_id)))
    
    user_id = get_user_id()
    res = get_playlist_with_tracks(playlist_id)  
    if res['playlist']['user_id'] != user_id:
            # User is not the owner of the playlist, just show the playlist
            return redirect(url_for('playlist.show_playlist', playlist_id=playlist_id))
        
    if request.method != 'POST':
        
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
            return redirect(url_for('playlist.show_playlist', playlist_id=playlist_id))

        except Exception as e:
            logger.error(f'error in playlist edit {e}')
            flash(str(e), 'error')
            res = get_playlist_with_tracks(playlist_id)
            
            l = {
             'page_title': 'Edit a playlist' + ' - ' + Lang.APP_NAME, 
    }    
            
            return render_template('playlist_edit.html',playlist=res['playlist'],l=l)
    
    
@playlist_bp.route('/playlist/<int:playlist_id>/delete')
def playlist_delete(playlist_id):
    if not is_connected():
        return redirect(url_for('users.login', next=url_for('playlist.playlist_delete', playlist_id=playlist_id)))
    
    playlist = db.get_playlist(playlist_id)
    if not playlist:
        flash('Playlist not found', 'error')
        return redirect(url_for('playlist.my_playlists'))
    
    if playlist['user_id'] != get_user_id():
        flash('You are not allowed to delete this playlist', 'error')
        return redirect(url_for('playlist.my_playlists'))
    
    try:
        message = delete_playlist(playlist_id)
        if 'error' in message:
            flash(message['error'], 'error')
            return redirect(url_for('playlist.playlist_edit', playlist_id=playlist_id))
        
        flash('Playlist deleted successfully', 'success')
        return redirect(url_for('playlist.my_playlists'))
    except Exception as e:
        flash(str(e), 'error')
    return redirect(url_for('playlist.playlist_edit', playlist_id=playlist_id))



@playlist_bp.route('/playlist_to_spotify/<int:playlist_id>')
def playlist_to_spotify(playlist_id,non_ajax=False):
    
    try:
        # connect to spotify
        token_spotify = ensure_valid_token()
        
        # Not connected to Spotify
        if token_spotify is None :
            redirect_url = url_for('spotify.spotify_auth', next=url_for('playlist.playlist_to_spotify', playlist_id=playlist_id)) #non_ajax=True
            return jsonify({'redirect': redirect_url})
            #return redirect(url_for('spotify.spotify_auth', next=url_for('playlist.playlist_to_spotify',playlist_id=playlist_id)))
        
        
        res = get_playlist_with_tracks(playlist_id)
 
        playlist = res['playlist']
        tracks = res['tracks']
        
        if not isinstance(playlist, dict):
            return jsonify({'error': 'Playlist object is not valid'}), 400
        
        if playlist is None:
            return jsonify({'error': 'Playlist is None'}), 400
        
        if not tracks or len(tracks) == 0:
            return jsonify({'error': 'No tracks in the playlist'}), 400
        
        
        playlist_id_spotify = playlist.get('playlist_id_spotify',None)
        
        
        
        if playlist_id_spotify is None:
            return create_spotify_playlist_and_add_tracks(playlist.get('title'), tracks,playlist_id)
            
        else:
            spotify_playlist_tracks_ids = get_spotify_playlist_tracks_ids(playlist_id_spotify)
            local_tracks_ids = [track['key_track_spotify'] for track in tracks]
            tracks_to_add = list(set(local_tracks_ids) - set(spotify_playlist_tracks_ids))
            tracks_to_add = [item for item in tracks_to_add if item not in (None, '')]
            if not len(tracks_to_add):
                return jsonify({'error': 'No new tracks to add to Spotify playlist'}), 400

            
            return add_tracks_to_spotify_playlist(playlist_id_spotify, tracks_to_add)
            
           
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


### JAx routes

@playlist_bp.route('/jax/update_position', methods=['POST'])
def update_position():
    data = request.json
    
    if not is_connected():
        return jsonify({"error": "You are not connected"}), 401
    
    if not all(k in data for k in ("playlist_id", "track_id", "new_position")):
        return jsonify({"error": "Missing required parameters"}), 400
    
    playlist_id = data['playlist_id']
    track_id = data['track_id']
    new_position = data['new_position']
    
    playlist = get_playlist_with_tracks(playlist_id)
    if not playlist:
        return jsonify({"error": "Playlist not found"}), 404
    
    if playlist['playlist']['user_id'] != get_user_id():
        return jsonify({"error": "You are not allowed to update this playlist"}), 403

    
    try:
        update_playlist_positions_after_track_change_position(playlist_id, track_id, new_position)
        return jsonify({"message": "Track position updated successfully"}), 200
    except Exception as e:
        
        return jsonify({"error": str(e)}), 500
    
    
@playlist_bp.route('/jax/add_track_to_playlist', methods=['POST'])
def jax_add_track_to_playlist():
    
    if not is_connected():
        return jsonify({"error": "You are not connected"}), 401
    

    data = request.json
    playlist_id = data['playlist_id']
    track_id = data['track_id']
    
    playlist = get_playlist_with_tracks(playlist_id)
    if not playlist:
        return jsonify({"error": "Playlist not found"}), 404
    
    if playlist['playlist']['user_id'] != get_user_id():
        return jsonify({"error": "You are not allowed to update this playlist"}), 403
    
    try:
        response = add_track_to_playlist(playlist_id, track_id)
        if 'error' in response:
            return jsonify({"error": response['error']}), 409
        
        return jsonify({"message": response['message']}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
    
@playlist_bp.route('/jax/add_track_to_playlist_last_used', methods=['POST'])
def jax_add_track_to_playlist_last_used():
    
    
    data = request.json 
    
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


@playlist_bp.route('/jax/remove_track_from_playlist', methods=['POST'])
def jax_remove_track_from_playlist():
    data = request.json
    playlist_id = data['playlist_id']
    track_id = data['track_id']
    
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "User not connected"}), 401
    
    playlist = get_playlist_with_tracks(playlist_id)
    if not playlist:
        return jsonify({"error": "Playlist not found"}), 404
    
    if playlist['playlist']['user_id'] != user_id:
        return jsonify({"error": "You are not allowed to update this playlist"}), 403
    
    try:
        response = remove_track_from_playlist(playlist_id,track_id, user_id)
        if 'error' in response:
            logger.error(f"error in removing track response : {response['error']}")
            return jsonify({"error": response['error']}), 409
        
        return jsonify({"message": response['message']}), 200
    except Exception as e:
        logger.error(f' Unknown error in removing track : {str(e)}')
        return jsonify({"error": str(e)}), 500
    
    
@playlist_bp.route('/jax/create_playlist_from_set_tracks', methods=['POST'])
def jax_create_playlist_from_set_tracks():
    data = request.json
    set_id = data['set_id']
    
    user_id = get_user_id()
    if not user_id:
        set_uri = url_for('set.set',set_id=set_id)
        redirect_uri = url_for('users.login', next=set_uri)
        return jsonify({"error": "User not connected",'redirect':redirect_uri}), 401
    
    try:
        response = create_playlist_from_set_tracks(set_id, user_id)
          
        if 'error' in response:
            return jsonify({"error": response['error']}), 409
        
        
        playlist_url = url_for('playlist.show_playlist',playlist_id=response['playlist_id'])
        
        return jsonify({"message": response['message'],'redirect':playlist_url}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@playlist_bp.route('/jax/jax_add_all_set_tracks_to_playlist', methods=['POST'])
def jax_add_all_set_tracks_to_playlist():
    data = request.json
    set_id = data['set_id']
    playlist_id = data['playlist_id']
    
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "User not connected"}), 401
    
    try:
        response = add_all_tracks_from_set_to_playlist(set_id, playlist_id, user_id)
        if 'error' in response:
            return jsonify({"error": response['error']}), 409
        
        return jsonify({"message": response['message']}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
    
@playlist_bp.route('/playlist_to_apple/<int:playlist_id>', methods=['GET','POST']) 
def playlist_to_apple(playlist_id,non_ajax=False):
    user_token = get_apple_music_user_token()
    if not user_token:
        #return current_user.extra_fields
        return redirect(url_for('playlist.auth_apple', redirect=request.url))
    
    dev_token = get_apple_music_dev_token() 
    if not dev_token:
        return jsonify({'error': 'Developer token not found. contact the dev bro'}), 400
       
    res = get_playlist_with_tracks(playlist_id)
 
    playlist = res['playlist']
    tracks = res['tracks']
    
    if not isinstance(playlist, dict):
        return jsonify({'error': 'Playlist object is not valid'}), 400
    
    if playlist is None:
        return jsonify({'error': 'Playlist is None'}), 400
    
    if not tracks or len(tracks) == 0:
        return jsonify({'error': 'No tracks in the playlist'}), 400
    
    
    return create_apple_playlist_and_add_tracks(dev_token,user_token,playlist.get('title'), tracks,playlist)
        
    
@playlist_bp.route('/auth_apple', methods=['GET'])
def auth_apple():
    
    if not is_connected():
        return redirect(url_for('users.login', next=url_for('playlist.auth_apple')))

    dev_token = get_apple_music_dev_token()
    redirect = request.args.get('redirect', None)

    return render_template('auth_apple.html',dev_token=dev_token,redirect=redirect)  # Render the Apple authentication template


@playlist_bp.route('/auth_apple/callback', methods=['POST'])
def store_apple_user_token():
   # user = current_user
    
    if not current_user.is_authenticated:
        return False
    
    redirect = request.json.get('redirect', None)
    
    if  not redirect:
        return {'error':'redirect parameter is required'}, 400
    
    user_token = request.json.get('token', None)
    if not user_token:
        return jsonify({'error': 'No token provided'}), 400
    
    set_apple_music_user_token(current_user,user_token)   

    return jsonify({'message': 'Token received and saved successfully','redirect':redirect}), 200 