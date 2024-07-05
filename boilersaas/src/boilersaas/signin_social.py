from datetime import datetime,timedelta,timezone # if you just directly import datetime, you will get an error on datetime.now
from pprint import pprint
#from time import timezone
from flask_dance.contrib.google import make_google_blueprint,google
# from flask_dance.contrib.facebook import make_facebook_blueprint,facebook
from .utils.db import db
from .models import OAuth
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_login import current_user
from flask import flash, redirect, url_for,current_app as app
from .models import User,UserConnectMethod,UserType
from flask_login import login_user
from sqlalchemy import String, and_
from flask_babel import _
import logging


# Setup Flask-Dance Google Blueprint
google_blueprint = make_google_blueprint(
    client_id=app.config.get('GOOGLE_CLIENT_ID'),
    client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
    scope=["openid","https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
    redirect_to="google.after_authorize"
)



google_blueprint.storage = SQLAlchemyStorage(OAuth, db.session, user=current_user,user_required=False)



@google_blueprint.route('/google/after_authorize')
def after_authorize():
    if not app.config.get('SIGNUP_OPTIONS')['allow_google']:
        flash(_('Google registration is not currently allowed.'), 'error')
        return redirect(url_for('main.index'))
    


    if not google.authorized:
       return redirect(url_for('google.login'))
    
    try:
        resp = google.get("/oauth2/v2/userinfo")
    except Exception as e:
        logging.error(f"An error occurred while accessing your Google account: {e}")
        flash(_('An error occurred while accessing your Google account.'), 'error')
        return redirect(url_for('google.login'))

        
    assert resp.ok, resp.text
    info = resp.json()
    info['locale'] = 'en' # default to english @TODO : get the locale from the user's browser or something
    
    user = User.query.filter_by(email=info["email"]).first()
    if not user:
        user = User(fname=info['given_name'], email=info["email"], password='0000',connect_method=UserConnectMethod.Google, type=UserType.User, lang=info['locale'])
        db.session.add(user)
        db.session.commit()
        
    
    login_user(user, remember=True)
    
    # Since we must update the user id in the OAuth table, we must find the OAuth record with the token
    # the comparison is kind of intensive here.
    # So let's narrow the fook down the search for when our app gets popular and we have a lot of new users
    five_minutes_ago_utc = (datetime.now(timezone.utc) - timedelta(minutes=5)).replace(tzinfo=None)  #  UTC datetime minus the .utc info at the end

    access_token = google.token.get('access_token')
    id_token = google.token.get('id_token')
    oauth = OAuth.query.filter(
    OAuth.created_at >= five_minutes_ago_utc,
    OAuth.user_id.is_(None),
    and_(
    OAuth.token.op('->>')('access_token') == access_token,
    OAuth.token.op('->>')('id_token') == id_token
    )
    ).first()
  
    if oauth:
        oauth.user_id = user.id
        db.session.commit()
    else:
        logging.error(f"No matching OAuth record found for access_token: {access_token} and id_token: {id_token}")
        flash(_('An error occurred while accessing your Google account.'), 'error')
        return redirect(url_for('google.login'))

        
   # Todo : check the cookie for the provenance page
    return redirect(url_for('main.dashboard'))  





# Cleanup task for orphaned sessions
# Can happen since the session if often created before the user without some ACID transaction
def cleanup_orphaned_sessions():
    
    one_day_ago_utc = (datetime.now(timezone.utc) - timedelta(days=1)).replace(tzinfo=None) 
    
    orphaned_sessions = OAuth.query.filter(
        OAuth.user_id.is_(None),
        OAuth.created_at < one_day_ago_utc
    ).all()
    
    for session in orphaned_sessions:
        db.session.delete(session)
    db.session.commit()

