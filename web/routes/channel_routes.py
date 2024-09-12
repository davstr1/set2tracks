from flask import Blueprint, redirect, render_template, request, url_for
from flask.cli import F
from flask_login import current_user

from web.controller import get_channels
from web.routes.routes_utils import tpl_utils



channel_bp = Blueprint('channel', __name__)


@channel_bp.route('/channels')
@channel_bp.route('/channels/page/<int:page>')
def channels(page=1):
    order_by = request.args.get('order_by', 'popular')
    per_page = request.args.get('per_page', 20)

    channels = get_channels(page, order_by, int(per_page), False)
    
    
    def get_pagination_url(page):
        params = {}

        if order_by != 'popular':
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
    
    
    return render_template('channels.html', channels=channels, tpl_utils=tpl_utils, pagination=pagination, is_paginated=is_paginated)
