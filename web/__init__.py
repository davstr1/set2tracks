import logging
from flask import Flask
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

from web.lib.log_config import setup_logging

bp = Blueprint('main', __name__,template_folder='templates')
from web import routes



def init_extend_app(app):
    app.register_blueprint(bp)
    add_babel_translation_directory('translations',app)
    babel = Babel(app)
    babel.init_app(app,locale_selector=get_locale) 


def create_app(config_class=Config):
    setup_logging()
    app = Flask(__name__)
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
 
    #
  
    
    

    
    #from app.users.models import User, Invite
    
    migrate = Migrate(app, db,directory='../init_ressources/migrations')
    with app.app_context():
         db.create_all()



    return app
