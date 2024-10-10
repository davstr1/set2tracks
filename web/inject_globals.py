from datetime import datetime
from flask import current_app as app
from web.routes.routes_utils import is_admin


def inject_globals():
    # Function to inject global variables or functions into templates
    return {
        'is_admin': is_admin,
        'notif_sound': app.config.get('NOTIF_SOUND'),
        'current_year': datetime.now().year   
        
        # Add more variables or functions as needed
    }