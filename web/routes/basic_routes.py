from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user



basic_bp = Blueprint('basic', __name__)


@basic_bp.route('/index')
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



@basic_bp.route('/quickstart')
def quickstart():
    return 'yo quickstart'
    return render_template('quickstart.html')

@basic_bp.route('/help')
def help():
    return 'yo help'
    return render_template('help.html')