from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user
from flask_cors import cross_origin
from requests import get
from web.lib.json_schemas import generate_video_object_with_tracklist
from lang import Lang
from web.controller import count_sets_with_all_statuses, get_all_featured_set_searches, get_browsing_history, get_channel_by_id, get_my_sets_in_queue_not_notified, get_playable_sets, get_playable_sets_number, get_playlists_from_user, get_set_id_by_video_id, get_set_queue_status, get_set_status, get_set_with_tracks, get_sets_in_queue, get_sets_with_zero_track, get_track_by_id, is_set_exists, is_set_in_queue, pre_queue_set, upsert_set_browsing_history
from web.lib.format import format_db_track_for_template, format_db_tracks_for_template, format_set_queue_error
from web.lib.related_tracks import save_related_tracks
from web.lib.utils import discarded_reason_to_ux
from web.lib.youtube import youtube_video_id_from_url, youtube_video_input_is_valid
from web.model import SetQueue
from web.routes.routes_utils import tpl_utils,get_user_id, is_connected, jax_redirect_if_not_connected,is_admin
from web.logger import logger
from markupsafe import Markup

set_bp = Blueprint('set', __name__)



## PAGES ##
## Scroll down to see the ACTIONS pages ##

@set_bp.route('/explore')
def sets():   
    
    PER_PAGE = 30
    page = request.args.get('page', 1, type=int)
    search = request.args.get('s', '', type=str)
    order_by = request.args.get('order_by', 'latest_youtube', type=str)
    
    sets_page,results_count = get_playable_sets(page=page, per_page=PER_PAGE,search=search,order_by=order_by,deduplicate=True)
    nb_sets_total = get_playable_sets_number()
    
    track,channel,page_title = None,None,None
    
    if search and search.startswith('trackid:'):
        track_id = int(search.split(':')[1])
        track = get_track_by_id(track_id)
        page_title = f"DJ Sets featuring \"{track['title']} - {track['artist_name']}\" - {Lang.APP_NAME}"
        page_meta = f"Discover DJ sets featuring \"{track['title']} - {track['artist_name']}\", get full tracklists, preview tracks, and export to Spotify or Apple Music"
        
        if track:
            page_title = f"DJ Sets featuring \"{track['title']} - {track['artist_name']}\" - {Lang.APP_NAME}"
            page_meta = f"Discover DJ sets featuring \"{track['title']} - {track['artist_name']}\", get full tracklists, preview tracks, and export to Spotify or Apple Music"
    elif search and search.startswith('channelid:'):
        channel_id = search.split(':')[1]
        channel = get_channel_by_id(channel_id)
        if channel:
            page_title = f"DJ Sets by {channel.author} - {Lang.APP_NAME}"
            page_meta = f"Explore DJ sets by {channel.author}, discover tracklists, preview songs and export to Spotify or Apple Music"
        
        
    
    #inspiration_searches = get_random_set_searches(20,20)
    inspiration_searches = get_all_featured_set_searches()
    
    
    def get_pagination_url(page):
        params = {}
        if search:
            params['s'] = search
        if order_by != 'latest_youtube':
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
    
    
    search_cap = search[:1].upper() + search[1:]
    if not page_title:
        if search:
            page_title = f"{search_cap} DJ sets - {Lang.APP_NAME}"
            page_meta = f"Explore  {search_cap} DJ sets, explore tracklists, preview tracks and export to Spotify or Apple Music"
        else:
            page_title = f'{Lang.APP_NAME} - Find tracks from DJ sets | Music discovery for DJs'
            page_meta = f'Find tracks from your favorite DJ sets ! Explore {nb_sets_total} sets ! Discover tracklists, preview music, and export to Spotify & Apple Music.'
    l = {
        'page_title': page_title,
        'page_description': page_meta
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
                           track=track,
                           channel=channel,
                            page="sets",
                            page_name="explore",
                            subpage_name="sets",
                           l=l) 
    
    
@set_bp.route('/history')
def browsing_history():
    # Constants
    PER_PAGE = 30
    user_id = current_user.id  # Assuming the user is logged in and `current_user` is available
    
    # Request parameters
    page = request.args.get('page', 1, type=int)
    search = request.args.get('s', '', type=str)
    order_by = request.args.get('order_by', 'recent', type=str)
    
    # Get browsing history with pagination and search
    sets_page, results_count = get_browsing_history(
        user_id=user_id, 
        page=page, 
        per_page=PER_PAGE, 
        order_by=order_by, 
        search=search
    )
    
    # Generate pagination URLs
    def get_pagination_url(page):
        params = {}
        if search:
            params['s'] = search
        if order_by != 'recent':
            params['order_by'] = order_by
        if page != 1:
            params['page'] = page
        return url_for('set.browsing_history', **params)

    # Pagination logic
    pagination = {}
    if sets_page.has_prev:
        pagination['prev_url'] = get_pagination_url(page - 1)
    if sets_page.has_next:
        pagination['next_url'] = get_pagination_url(page + 1)
    
    is_paginated = sets_page.has_next or sets_page.has_prev
    
    # Page title
    page_title = 'My Browsing History - ' + Lang.APP_NAME
    
    l = {
        'page_title': page_title,
    }  
    
    # Render the template
    return render_template('sets.html', 
                           sets_page=sets_page,
                           results_count=results_count,
                           search=search, 
                           order_by=order_by,
                           pagination=pagination,
                           is_paginated=is_paginated,
                           page_title=page_title,
                           tpl_utils=tpl_utils,l=l)

    
# Add get params for page and status
@set_bp.route('/sets/queue')  
def sets_queue():
    if not is_connected():
        return redirect(url_for('users.login', next=url_for('set.sets_queue')))
    
    
    page = request.args.get('page', default=1, type=int)
    status = request.args.get('status', default=None, type=str)
    if is_admin():
        include_15min_error = request.args.get('include_15min_error', default=False, type=bool)
    else:
        include_15min_error = True
    
    if status and status == 'zero_track':
        sets,nb_sets = get_sets_with_zero_track(page=page)
    else:     
        sets,nb_sets = get_sets_in_queue(page=page, status=status, include_15min_error=include_15min_error)
    #my_sets = get_my_sets_in_queue(user_id=get_user_id())
    my_sets = None
    
    count = count_sets_with_all_statuses(include_15min_error=include_15min_error)
    
    def get_pagination_url(page):
     params = {}
     
     if status:
         params['status'] = status
     if page != 1:
         params['page'] = page
     if include_15min_error:
            params['include_15min_error'] = include_15min_error
     return url_for('set.sets_queue', **params)

    pagination = {}
    if sets.has_prev:
        pagination['prev_url'] = get_pagination_url(page - 1)
    if sets.has_next:
        pagination['next_url'] = get_pagination_url(page + 1)
    
    is_paginated = sets.has_next or sets.has_prev
    
    l = {
        'page_title': 'Sets in Queue' + ' - ' + Lang.APP_NAME,
    }      
    
    
        
    return render_template('sets_queue.html',sets=sets,my_sets=my_sets,
                           l=l,
                           is_paginated=is_paginated,
                           pagination=pagination,
                           tpl_utils=tpl_utils,
                           status=status,
                          
                           format_set_queue_error=format_set_queue_error,
                           discarded_reason_to_ux=discarded_reason_to_ux,
                           include_15min_error=include_15min_error,
                           count=count)
    
    

    


@set_bp.route('/set/<int:set_id>')
def set(set_id):
    set = get_set_with_tracks(set_id)
     
    if 'error' in set:
        return redirect(url_for('set.sets'))
    
    set_queue_status = get_set_queue_status(set['video_id'])
    
        
    if not is_admin() and set_queue_status and set_queue_status != 'done':
        flash('This set is not publically accessible. Please try again later.', 'error')
        return redirect(url_for('set.sets'))
    
    #genres = get_set_genres_by_occurrence(set_id)
    #pprint(genres)
   # avg_properties = calculate_avg_properties(set['tracks'])
    #most_common_decades = calculate_decade_distribution(set['tracks'])
    #pprint(most_common_decades)
    # most_common_tempos = calculate_and_sort_tempo_distribution(set['tracks'])
    # pprint(avg_properties)
    # pprint('------')
    # print(most_common_decades)
    # print(most_common_tempos)
    #pprint(get_set_avg_characteristics(set_id))
    
    channel = get_channel_by_id(set['channel_id'])
    channel.sets_visible = sorted(
            [set_item for set_item in channel.sets if (not set_item.hidden and set_item.published)],
            key=lambda set_item: set_item.publish_date,
            reverse=True
        )
    channel.nb_sets_visible = len(channel.sets_visible)
    
    current_url = request.url
    user_id = get_user_id()
    
    if user_id:
        user_playlists = get_playlists_from_user(user_id, order_by='edit_date',page=1,per_page=100)
        upsert_set_browsing_history(set_id,user_id)
    else:
        user_playlists = []
        
    l = {
        'page_title':  set.get('title') + '" - ' + set['channel'].author + ' - Playlist & Video ' ,
        'page_description': f'Watch  {set.get("title")} and explore the full playlist curated by EstiloSónico. Discover tracklist details, preview songs, and export to Spotify or Apple Music.'
    }      

    canonical_url = url_for('set.set', set_id=set_id, _external=True)
    json_schema = generate_video_object_with_tracklist(set, canonical_url)
   

    return render_template('set.html', set=set,channel=channel,tpl_utils=tpl_utils,user_playlists=user_playlists,current_url=current_url,l=l,json_schema=json_schema,canonical_url=canonical_url)




@set_bp.route('/related_tracks/<int:track_id>')
def related_tracks(track_id):
    track = get_track_by_id(track_id,format_for_template=False)
    if not track:
        logger.error(f"Track with ID {track_id} does not exist.")
        return redirect(request.referrer or url_for('basic.index'))
    
    if track.related_tracks and len(track.related_tracks) > 0:
        related_tracks =format_db_tracks_for_template(track.related_tracks)
        track_formated = format_db_track_for_template(track)
        current_url = request.url
        user_id = get_user_id()
    
        if user_id:
            user_playlists = get_playlists_from_user(user_id, order_by='edit_date',page=1,per_page=100)
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
# Shouw the form or just do the basic verification befor inserting the set
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
        send_email = request.form.get('send_email')
        play_sound = request.form.get('play_sound')
        manually_added = request.form.get('manually_added')
        
        return redirect(url_for('set.insert_set_route',video_id=video_id,send_email=send_email,play_sound=play_sound,manually_added=manually_added))
    
    youtube_url = request.args.get('youtube_url', '')
    
    l = {
        'page_title': 'Add a set' + ' - ' + Lang.APP_NAME,
    }    
    
    
    return render_template('add.html',youtube_url=youtube_url,l=l)


@set_bp.route('/insert_set/<video_id>', methods=['GET'])
def insert_set_route(video_id):
     
    if not is_connected():
        return redirect(url_for('users.login', next=url_for('set.add')))
    
    # check if the set already is in queue or discarded
    queued_set = is_set_in_queue(video_id)
    print('queued_set',queued_set)
    if queued_set and queued_set.status != 'done':
        if queued_set.status == 'discarded':
            ux_discarded_reason = discarded_reason_to_ux(queued_set.discarded_reason)
            if 'live' not in ux_discarded_reason.lower(): # live sets can be retried
                flash(Markup(f'This video was discarded : <strong>{ux_discarded_reason}</strong>'), 'error')
                return redirect(url_for('set.add', youtube_url=video_id))
        elif queued_set.status == 'premiered':
            flash(f'This set {queued_set.discarded_reason}. Come back later', 'warning')
            return redirect(url_for('set.add', youtube_url=video_id))
        else:
            flash('This set is already in the queue. Will be published in a moment', 'warning')
            return redirect(url_for('set.add', youtube_url=video_id))
    
    # published
    if (is_set_exists(video_id)):
        flash('Yeehaaaa ! the set is already there', 'info')
        return redirect(url_for('set.set',set_id=get_set_id_by_video_id(video_id))) 
   
    send_email = request.args.get('send_email')
    play_sound = request.args.get('play_sound')
    manually_added = request.args.get('manually_added')
    
    # the extension sends us here. 
    # However we need the user to fill the play sound and send email options
    if not manually_added:
        return redirect(url_for('set.add', youtube_url=video_id))
    
    result = pre_queue_set(video_id,get_user_id(),send_email,play_sound) #insert_set(video_id)
   
   
    if isinstance(result, dict) and 'error' in result:
        flash(result['error'], 'error')
        return redirect(url_for('set.add', youtube_url=video_id))

    if isinstance(result, SetQueue) and result.id:
        flash('Set added to the pre queue', 'success')
        return redirect(url_for('set.add'))
    










@set_bp.route('/jax/check_user_queue')
def jax_check_user_queue():
    if not is_connected():
        return {}, 500

    user_id = get_user_id()
    if not user_id:
        return jsonify({}), 401
    
    my_sets = get_my_sets_in_queue_not_notified(user_id)
    if not my_sets:
        return jsonify({}), 401
    
    return jsonify(my_sets), 200

    
    
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
    
    data = request.json 
    caller_url = data['caller_url'] if 'caller_url' in data else None
    
    if not is_connected():
        return jax_redirect_if_not_connected(next_url=caller_url)
    
    track = get_track_by_id(track_id,format_for_template=False)
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
            # flash(ret['error'], 'error')
            return jsonify({'error':f"{ret['error']}"}), 409
        
        return jsonify(ret),200
    except Exception as e:
        return jsonify({'error':f"Error saving related tracks: {e}"}), 500