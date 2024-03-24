from flask import Blueprint
from flask_babel import Babel
from boilersaas.utils.locale import get_locale,add_babel_translation_directory
bp = Blueprint('extend', __name__,template_folder='templates')
from web.extend import routes,bp


def init_app(app):
    app.register_blueprint(bp)
    add_babel_translation_directory('extend/translations',app)
    babel = Babel(app)
    babel.init_app(app,locale_selector=get_locale) 