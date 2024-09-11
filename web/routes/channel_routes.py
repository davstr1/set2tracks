from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user



channel_bp = Blueprint('channel', __name__)


@channel_bp.route('/channels')
def channels():
    return render_template('channels.html')