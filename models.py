from utils.db import db
from flask_login import UserMixin
from flask import current_app as app
from datetime import datetime  
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin


class User(db.Model,UserMixin):
    __tablename__ = app.config.get('DB_TABLE_USERS')

    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Store hashed passwords
    type = db.Column(db.Enum(app.config.get('UserType')), nullable=False)
    reg_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    lang = db.Column(db.String(2), nullable=False, default='en')
    connect_method = db.Column(db.Enum(app.config.get('UserConnectMethod')), nullable=False)
    extra_fields = db.Column(db.JSON, nullable=True)
    
    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config.get('SECRET_KEY'))
        token = s.dumps({'user_id': self.id})
        s.loads(token,max_age=expires_sec)
        return token

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config.get('SECRET_KEY'))
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)


class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)


class Invite(db.Model):
    __tablename__ = app.config.get('DB_TABLE_INVITES')
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    invite_code = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  

    def __repr__(self):
        return f'<Invite {self.email}>'

