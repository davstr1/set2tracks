from flask import Flask
from config import Config

from app.core import init_app as init_main_app # important to import before. templates takes precedence
from app.extend import init_app as init_extend_app 
from boilersaas import init_boilerplate_app



from boilersaas.utils.db import db
#from app.utils.mail import mail
from flask_migrate import Migrate


def create_app(config_class=Config):
    app = Flask(__name__,static_url_path='/static',static_folder='./core/static')
    app.config.from_object(config_class)

    print (app.static_folder)
    db.init_app(app)
    #mail.init_app(app)
    init_extend_app(app)
    init_main_app(app)
    init_boilerplate_app(app)
 
    #
  
    
    

    
    #from app.users.models import User, Invite
    
    migrate = Migrate(app, db)
    # with app.app_context():
    #     db.create_all()


    return app
