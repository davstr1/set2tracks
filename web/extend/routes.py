from flask import render_template,redirect,url_for
from flask_login import login_required
from web.extend import bp
from flask_babel import lazy_gettext as _l



@bp.route('/')
def index():
    #return str(_l('index hello world!'))
    return render_template('index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    return str(_l('dashboard hello world!'))
   # return render_template('dashboard.html')
   
   
@bp.route('/foo')
def foo():
    return 'foo'
    
    
