from pprint import pprint
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user
from flask_cors import CORS, cross_origin
from lang import Lang
from web.controller import get_all_featured_set_searches, get_my_sets_in_queue, get_playable_sets, get_playable_sets_number, get_playlists_from_user, get_random_set_searches, get_set_id_by_video_id, get_set_status, get_set_with_tracks, get_sets_in_queue, get_track_by_id, is_set_exists, queue_set
from web.lib.format import format_db_track_for_template, format_db_tracks_for_template
from web.lib.related_tracks import save_related_tracks
from web.lib.utils import calculate_decade_distribution
from web.lib.youtube import youtube_video_id_from_url, youtube_video_input_is_valid
from web.model import SetQueue
from web.routes.routes_utils import tpl_utils,get_user_id, is_connected, jax_redirect_if_not_connected,is_admin
from web.logger import logger


set_bp = Blueprint('set', __name__)

## PAGES ##
## Scroll down to see the ACTIONS pages ##

@set_bp.route('/')
def sets():   
    
    PER_PAGE = 30
    page = request.args.get('page', 1, type=int)
    search = request.args.get('s', '', type=str)
    order_by = request.args.get('order_by', 'recent', type=str)
    
    sets_page,results_count = get_playable_sets(page=page, per_page=PER_PAGE,search=search,order_by=order_by)
    nb_sets_total = get_playable_sets_number()
    
    
    #inspiration_searches = get_random_set_searches(20,20)
    inspiration_searches = get_all_featured_set_searches()
    
    
    def get_pagination_url(page):
        params = {}
        if search:
            params['s'] = search
        if order_by != 'recent':
            params['order_by'] = order_by
        if page != 1:
            params['page'] = page
        return url_for('set.sets', **params)

    pagination = {}
    if sets_page.has_prev:
        pagination['prev_url'] = get_pagination_url(page - 1)
    if sets_page.has_next:
        pagination['next_url'] = get_pagination_url(page + 1)
    
    is_paginated = sets_page.has_next or sets_page.has_prev
    
    l = {
        'page_title': Lang.APP_NAME + ' - ' + 'Find tracks from your favorite DJ sets',
    }  
    
    #playlists_user = get_playlists_from_user(1)
    return render_template('sets.html', 
                           sets_page=sets_page,
                           nb_sets_total=nb_sets_total,
                           search=search,order_by=order_by,
                           results_count=results_count,
                           pagination=pagination,
                           is_paginated=is_paginated,
                           inspiration_searches=inspiration_searches,
                           tpl_utils=tpl_utils,
                           l=l) 
    
    
@set_bp.route('/sets/queue')  
def get_sets_queue():
    if not is_connected():
        return redirect(url_for('users.login', next=url_for('set.get_sets_queue')))
    sets = get_sets_in_queue()
    my_sets = get_my_sets_in_queue(user_id=get_user_id())
    
    l = {
        'page_title': 'Sets in Queue' + ' - ' + Lang.APP_NAME,
    }      
        
    return render_template('sets_queue.html',sets=sets,my_sets=my_sets,l=l)


@set_bp.route('/set/<int:set_id>')
def set(set_id):
    set = get_set_with_tracks(set_id)
    
    txt = request.args.get('txt', '', type=str)
    

    
    if 'error' in set:
        return redirect(url_for('basic.index'))
    
    #genres = get_set_genres_by_occurrence(set_id)
    #pprint(genres)
   
    

   # avg_properties = calculate_avg_properties(set['tracks'])
 
    most_common_decades = calculate_decade_distribution(set['tracks'])
    
    pprint(most_common_decades)
    # most_common_tempos = calculate_and_sort_tempo_distribution(set['tracks'])
    # pprint(avg_properties)
    # pprint('------')
    # print(most_common_decades)
    # print(most_common_tempos)
    #pprint(get_set_avg_characteristics(set_id))
    
    if txt:
        return render_template('set.txt', set=set)
    
    current_url = request.url
    user_id = get_user_id()
    
    if user_id:
        user_playlists = get_playlists_from_user(user_id, order_by='title')
    else:
        user_playlists = []
        
    l = {
        'page_title': set.get('title') + 'Tracklist  '  + Lang.APP_NAME,
    }      

    return render_template('set.html', set=set,tpl_utils=tpl_utils,user_playlists=user_playlists,current_url=current_url,is_admin=is_admin(),l=l)




@set_bp.route('/related_tracks/<int:track_id>')
def related_tracks(track_id):
    track = get_track_by_id(track_id)
    if not track:
        logger.error(f"Track with ID {track_id} does not exist.")
        return redirect(request.referrer or url_for('basic.index'))
    
    if track.related_tracks and len(track.related_tracks) > 0:
        related_tracks =format_db_tracks_for_template(track.related_tracks)
        track_formated = format_db_track_for_template(track)
        current_url = request.url
        user_id = get_user_id()
    
        if user_id:
            user_playlists = get_playlists_from_user(user_id, order_by='title')
        else:
            user_playlists = []
            
        l = {
        'page_title': track.title + ' : Related tracks - ' + Lang.APP_NAME,
        }  
            
        return render_template('related_tracks.html',track=track_formated,tracks=related_tracks,tpl_utils=tpl_utils,user_playlists=user_playlists,current_url=current_url,l=l)
    else:
        logger.info('no related tracks')
        return redirect(request.referrer or url_for('basic.index'))
    
    
## ACTIONS  pages ##



@set_bp.route('/add', methods=['GET', 'POST'])
def add():
    if not is_connected():
        return redirect(url_for('users.login', next=url_for('set.add')))
    
    

    if request.method == 'POST':
        youtube_url = request.form.get('youtube_url')
        if not youtube_url:
            flash('No YouTube URL provided. Please enter a URL.', 'error')
            return redirect(url_for('set.add', youtube_url=youtube_url))
        if not youtube_video_input_is_valid(youtube_url):
            flash('Invalid YouTube URL. Please enter a valid URL.', 'error')
            return redirect(url_for('set.add', youtube_url=youtube_url))
       
        
        # Process the YouTube URL as needed
        # Example of successful processing redirect or message
        #flash('URL received successfully.', 'success')
        video_id = youtube_video_id_from_url(youtube_url)
        return redirect(url_for('set.insert_set_route',video_id=video_id))
    
    youtube_url = request.args.get('youtube_url', '')
    
    l = {
        'page_title': 'Add a set' + ' - ' + Lang.APP_NAME,
    }      
    
    return render_template('add.html',youtube_url=youtube_url,l=l)


@set_bp.route('/insert_set/<video_id>', methods=['GET'])
def insert_set_route(video_id):
    
    if (is_set_exists(video_id)):
       return redirect(url_for('set.set',set_id=get_set_id_by_video_id(video_id))) 
    
    result = queue_set(video_id,get_user_id()) #insert_set(video_id)
   
   
    if isinstance(result, dict) and 'error' in result:
        flash(result['error'], 'error')
        return redirect(url_for('set.add', youtube_url=video_id))

    if isinstance(result, SetQueue) and result.id:
        flash('Set added to the queue', 'success')
        return redirect(url_for('set.add'))
    












    
    
@set_bp.route('/jax/check_set_status/<string:youtube_video_id>', methods=['GET','POST'])
@cross_origin()
def jax_check_set_status(youtube_video_id):
    """
    Check the status of a set based on the given YouTube video ID.

    Parameters:
    youtube_video_id (str): The ID of the YouTube video.

    Returns:
    dict: A JSON response containing the status of the set.

    Raises:
    None

    """
    if not youtube_video_input_is_valid(youtube_video_id):
        return jsonify({'error':f"Invalid YouTube ID"}), 400
    
    return jsonify(get_set_status(youtube_video_id))
    
    
    
@set_bp.route('/jax/check_save_related_tracks/<int:track_id>', methods=['GET','POST'])
def jax_check_save_related_tracks(track_id):
    
    print(request.json)
    
    data = request.json 
    caller_url = data['caller_url'] if 'caller_url' in data else None
    
    if not is_connected():
        return jax_redirect_if_not_connected(next_url=caller_url)
    
    track = get_track_by_id(track_id)
    if not track:
        return jsonify({'error':f"Track does not exist in our papers."}), 404
    
    has_related_tracks = track.has_related_tracks()
    if has_related_tracks and len(track.related_tracks) > 0:
        return jsonify({'message': f"Related tracks already saved this track"}), 200
    
    if has_related_tracks and len(track.related_tracks) == 0:
        return jsonify({'error': f"No related tracks found for this track"}), 500
    
    try:    
        ret = save_related_tracks(track)
       
        
        if 'error' in ret:
            flash(ret['error'], 'error')
            return jsonify({'error':f"{ret['error']}"}), 409
        
        return jsonify(ret),200
    except Exception as e:
        return jsonify({'error':f"Error saving related tracks: {e}"}), 500