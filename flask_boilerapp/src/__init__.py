from flask import Blueprint
from signin_social import google_blueprint
from flask_login import LoginManager,current_user
from flask_babel import Babel
from utils.locale import add_babel_translation_directory, get_locale
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_dance.consumer import oauth_authorized
from utils import db
from flask_mail import Mail



login_manager = LoginManager()
login_manager.login_view = 'users.login'

bp = Blueprint('users', __name__,template_folder='templates')
from . import models,routes  



@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))

mail = None

def init_boilerplate_app(app):

    app.register_blueprint(bp)
    app.register_blueprint(google_blueprint,url_prefix="/login")  
    
    
    add_babel_translation_directory('users/translations',app)
    babel = Babel(app)
    babel.init_app(app,locale_selector=get_locale)  
    
    
    login_manager.init_app(app) 
    
    global mail
    mail = Mail(app)
    
    @app.context_processor
    def inject_user_status():
        return dict(is_logged_in=current_user.is_authenticated)
    
    

    

