from flask import Blueprint
from flask_babel import Babel
from web.core.utils.locale import get_locale,add_babel_translation_directory
bp_core = Blueprint('main', __name__,template_folder='templates')
from web.core import routes


def init_app(app):
    app.register_blueprint(bp_core)
    add_babel_translation_directory('main/translations',app)
    #babel = Babel(app)
   #babel.init_app(app,locale_selector=get_locale) 