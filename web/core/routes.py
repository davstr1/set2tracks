from flask import render_template,redirect,url_for
from flask_login import login_required
from web.core import bp_core
from flask_babel import lazy_gettext as _l



@bp_core.route('/')
def index():
    #return str(_l('index hello world!'))
    return render_template('index.html')

@bp_core.route('/dashboard')
@login_required
def dashboard():
    #return str(_l('dashboard hello world!'))
    return render_template('dashboard.html')
    
    
