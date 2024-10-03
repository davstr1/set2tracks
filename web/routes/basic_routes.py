from re import L
from flask import Blueprint, Config, redirect, render_template, request, url_for
from flask_login import current_user

from lang import Lang



basic_bp = Blueprint('basic', __name__)


@basic_bp.route('/')
def index():
    return 'index'
    return redirect(url_for('set.sets'))


@basic_bp.route('/dashboard')
def dashboard():
    if current_user.is_authenticated:
        next_page_cookie = request.cookies.get('next_page_after_login')
        if next_page_cookie:
            response = redirect(next_page_cookie)
            response.delete_cookie('next_page_after_login')
            return response
            
            
        return render_template('dashboard.html')
    
    return redirect(url_for('basic.index'))





@basic_bp.route('/help')
def help():
    return 'yo help'
    return render_template('help.html')


@basic_bp.route('/plans')
def plans():
    # TODO: Add useer integration
    l = {
        'page_title': 'Plans - ' + Lang.APP_NAME,
    }
    return render_template('plans.html', l=l)