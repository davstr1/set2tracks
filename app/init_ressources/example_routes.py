from flask import render_template,redirect,url_for
from flask_login import current_user, login_required
from web import bp
from flask_babel import lazy_gettext as _l

@bp.route('/')
def index():
    return render_template('index.html')
       
@bp.route('/dashboard')
def dashboard():
    if current_user.is_authenticated:
        return render_template('dashboard.html')
    
    return redirect(url_for('basic.index'))


# Define your own routes here
@bp.route('/foo')
def foo():
    return 'foo'