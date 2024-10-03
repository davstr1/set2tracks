from re import L
from flask import Blueprint, Config, redirect, render_template, request, url_for
from flask_login import current_user

from lang import Lang



track_bp = Blueprint('track', __name__)


@track_bp.route('/explore/tracks')
def tracks():
    return 'track'
    return redirect(url_for('set.sets'))


