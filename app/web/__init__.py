import logging
import traceback
from flask import Flask, render_template
from config import Config

# important to import before. templates takes precedence
#from web.init import init_app as init_extend_app 
from boilersaas import init_boilerplate_app



from boilersaas.utils.db import db
#from app.utils.mail import mail
from flask_migrate import Migrate


from flask import Blueprint
from flask_babel import Babel
from boilersaas.utils.locale import get_locale,add_babel_translation_directory

from web.inject_globals import inject_globals
from web.lib.log_config import setup_logging


bp = Blueprint('main', __name__,template_folder='templates')
from web.routes import basic_bp, set_bp, spotify_bp, playlist_bp,admin_bp,channel_bp,track_bp

def set_global_exception_handler(app):
    @app.errorhandler(Exception)
    def unhandled_exception(e):
        response = dict()
        
        #traceback_formated = "<br>".join(traceback_full.splitlines())
        error_message = str(e)
        error_type = type(e).__name__
        error_message = str(e)
        error_message = f"{error_type}: {error_message}"
        
        traceback_full = traceback.format_exc()
        traceback_formated = traceback_full.replace("Traceback (most recent call last):", "")
        traceback_formated = traceback_formated.replace(error_message, "")
        traceback_formated = traceback_formated.replace("\n", "<br>")   
        
        logger = logging.getLogger("myapp.error_handled")
        logger.error("Caught Exception: {}".format(error_message)) #or whatever logger you use
        return render_template('error.html', error_message=error_message,traceback_formated=traceback_formated), 500

def init_extend_app(app):
    app.register_blueprint(basic_bp)
    app.register_blueprint(set_bp)
    app.register_blueprint(spotify_bp)
    app.register_blueprint(playlist_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(channel_bp)
    app.register_blueprint(track_bp)
    add_babel_translation_directory('translations',app)
    babel = Babel(app)
    babel.init_app(app,locale_selector=get_locale) 


def create_app(config_class=Config):
    setup_logging()
    app = Flask(__name__)
    set_global_exception_handler(app)
    app.config.from_object(config_class)
    
    db.init_app(app)
    #mail.init_app(app)
    init_extend_app(app)
    
    init_boilerplate_app(app)
    
     # Modify Jinja2 environment settings to suppress detailed template loading messages
    app.jinja_env.globals['debug'] = False
    app.jinja_env.loader.debug = False
    app.jinja_env.add_extension('jinja2.ext.do')
    app.jinja_env.add_extension('jinja2.ext.loopcontrols')
    app.context_processor(inject_globals)
    #
  
    
    

    
    #from app.users.models import User, Invite
    
    migrate = Migrate(app, db,directory='../init_ressources/migrations')
    with app.app_context():
         db.create_all()



    return app
