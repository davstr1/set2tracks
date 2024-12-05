import logging
import traceback
from flask import Flask, render_template
from config import Config
from sqlalchemy.exc import OperationalError
from werkzeug.middleware.proxy_fix import ProxyFix # allows https to be detected by flask on Digital Ocean (reverse proxy)

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
    """
    Factory function to create and configure the Flask application instance.

    Args:
        config_class: The configuration class to use for the app settings.

    Returns:
        app: A configured Flask application instance.
    """
    from flask import Flask

    try:
        print("Starting app creation...")
        # Initialize logging to capture and manage application logs
        print("Setting up logging...")
        setup_logging()
        print("Logging setup complete.")
    except Exception as e:
        print(f"Failed to set up logging: {e}")
        raise

    try:
        # Create a Flask application instance
        print("Creating Flask app instance...")
        app = Flask(__name__)
        print("Flask app instance created.")
    except Exception as e:
        print(f"Failed to create Flask app instance: {e}")
        raise

    try:
        # Set up a global exception handler
        print("Setting global exception handler...")
        set_global_exception_handler(app)
        print("Global exception handler set.")
    except Exception as e:
        print(f"Failed to set global exception handler: {e}")
        raise

    try:
        # Load application configuration
        print(f"Loading app configuration from {config_class.__name__}...")
        app.config.from_object(config_class)
        print("App configuration loaded.")
    except Exception as e:
        print(f"Failed to load app configuration: {e}")
        raise
    
    try:
        app.wsgi_app = ProxyFix(app.wsgi_app)
        print("ProxyFix added.")
    except Exception as e:
        print(f"Failed to add ProxyFix: {e}")
        raise
        

    try:
        # Initialize the database (SQLAlchemy)
        print("Initializing database...")
        db.init_app(app)
        print("Database initialized.")
    except Exception as e:
        print(f"Failed to initialize the database: {e}")
        raise

    try:
        # (Optional) Initialize the mail extension if required
        # print("Initializing mail extension...")
        # mail.init_app(app)
        # print("Mail extension initialized.")
        pass  # Uncomment and configure if mail is required
    except Exception as e:
        print(f"Failed to initialize mail extension: {e}")
        raise

    try:
        # Extend app functionality
        print("Extending app functionality...")
        init_extend_app(app)
        print("App functionality extended.")
    except Exception as e:
        print(f"Failed to extend app functionality: {e}")
        raise

    try:
        # Boilerplate initialization for common patterns
        print("Initializing boilerplate app settings...")
        init_boilerplate_app(app)
        print("Boilerplate app settings initialized.")
    except Exception as e:
        print(f"Failed to initialize boilerplate app settings: {e}")
        raise

    try:
        # Configure the Jinja2 template environment
        print("Configuring Jinja2 template environment...")
        app.jinja_env.globals['debug'] = False
        app.jinja_env.loader.debug = False
        app.jinja_env.add_extension('jinja2.ext.do')
        app.jinja_env.add_extension('jinja2.ext.loopcontrols')
        print("Jinja2 template environment configured.")
    except Exception as e:
        print(f"Failed to configure Jinja2 template environment: {e}")
        raise

    try:
        # Inject global variables or functions into templates
        print("Injecting global variables into templates...")
        app.context_processor(inject_globals)
        print("Global variables injected.")
    except Exception as e:
        print(f"Failed to inject global variables: {e}")
        raise

  


  
    
    

    
    #from app.users.models import User, Invite
    
    migrate = Migrate(app, db,directory='../init_ressources/migrations')
    with app.app_context():
        print("Creating database tables...")
        try:
            db.create_all()
            print("Database tables created successfully.")
        except OperationalError as e:
            print(f"Database connection failed: {e}")


    print("App creation complete.")
    return app
