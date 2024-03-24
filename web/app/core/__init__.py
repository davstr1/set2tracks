from flask import Blueprint
from flask_babel import Babel
from app.utils.locale import get_locale,add_babel_translation_directory
bp = Blueprint('main', __name__,template_folder='templates')
from app.core import routes,bp


def init_app(app):
    app.register_blueprint(bp)
    add_babel_translation_directory('core/translations',app)
    babel = Babel(app)
    babel.init_app(app,locale_selector=get_locale) 