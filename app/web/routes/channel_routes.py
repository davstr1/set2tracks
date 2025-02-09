from flask import Blueprint, render_template, request, url_for

from web.controller.channel import get_channels
from lang import Lang
from web.routes.routes_utils import tpl_utils



channel_bp = Blueprint('channel', __name__)


@channel_bp.route('/explore/channels')
@channel_bp.route('/channels/page/<int:page>')
def channels(page=1):
    order_by = request.args.get('order_by', 'channel_popularity')
    per_page = request.args.get('per_page', 20)
    search = request.args.get('s', '')
    page = int(page) or 1
    channels,results_count = get_channels(page, order_by, int(per_page),search, False)
    
    # Filter each channel's sets to only include ones where set.hidden is False
    for channel in channels:
        channel.sets_visible = sorted(
            [set_item for set_item in channel.sets if (not set_item.hidden and set_item.published)],
            key=lambda set_item: set_item.publish_date,
            reverse=True
        )
        channel.nb_sets_visible = len(channel.sets_visible)
        
    
    
    def get_pagination_url(page):
        params = {}

        if order_by != 'channel_popularity':
            params['order_by'] = order_by
        if page != 1:
            params['page'] = page
        return url_for('channel.channels', **params)

    pagination = {}
    if channels.has_prev:
        pagination['prev_url'] = get_pagination_url(page - 1)
    if channels.has_next:
        pagination['next_url'] = get_pagination_url(page + 1)
    
    is_paginated = channels.has_next or channels.has_prev
    
    canonical_url = url_for('channel.channels')
    
    if not search:
    
        if order_by == 'channel_popularity':
            page_title = f'Top {str(results_count)} Youtube DJ Channels - ' + Lang.APP_NAME
            page_meta = f'Discover the most popular Youtube DJ Channels. Explore top DJs, tracklists, and new music' 
    
        elif order_by == 'az':
            page_title = f'A-Z List of Youtube DJ Channels - ' + Lang.APP_NAME
            page_meta = f'Find the best DJ channels on YouTube, sorted alphabetically. Explore tracklists, artists, and mixes.'
        else:
            page_title = f'Newly Added added DJ channels" - ' + Lang.APP_NAME
            page_meta = f'Browse recently added YouTube DJ channels. Discover fresh DJ mixes, tracklists, and music trends.'
            
    else:
        page_title = f'"Search Results for {search} in DJ channels" - ' + Lang.APP_NAME
        page_meta = f'Find YouTube DJ channels related to  "{search}. Explore tracklists, new mixes, and trending DJs"'
    
    
    l = {
        'page_title' : page_title,
        'page_description' : page_meta,
    }
    
    
    return render_template('channels.html', 
                           channels=channels, 
                           results_count=results_count,
                           search=search,
                           tpl_utils=tpl_utils, 
                           pagination=pagination, 
                           is_paginated=is_paginated, 
                           canonical_url=canonical_url,
                           order_by=order_by,
                           page=page,
                           per_page=per_page,
                           page_name = 'explore',
                           subpage_name = 'channels',
                           l=l)
