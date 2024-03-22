import datetime
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
    
    
    resp = google.get("/oauth2/v2/userinfo")

        
    assert resp.ok, resp.text
    info = resp.json()
    print("info",info)
    user = User.query.filter_by(email=info["email"]).first()
    if not user:
        user = User(fname=info['given_name'], email=info["email"], password='0000',connect_method=UserConnectMethod.Google, type=UserType.User, lang=info['locale'])
        db.session.add(user)
        db.session.commit()
        
    
    login_user(user, remember=True)
    
    # Since we must update the user id in the OAuth table, we must find the OAuth record with the token
    # the comparison is kind of intensive here.
    # So let's narrow the fook down the search for when our app gets popular and we have a lot of new users
    five_minutes_ago_utc = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
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
        raise Exception("No matching OAuth record found.")

        
   
    return redirect(url_for('main.dashboard'))  





# Cleanup task for orphaned sessions
# Can happen since the session if often created before the user without some ACID transaction
def cleanup_orphaned_sessions():
    
    one_day_ago_utc = datetime.utcnow() - datetime.timedelta(days=1)
    
    orphaned_sessions = OAuth.query.filter(
        OAuth.user_id.is_(None),
        OAuth.created_at < one_day_ago_utc
    ).all()
    
    for session in orphaned_sessions:
        db.session.delete(session)
    db.session.commit()

