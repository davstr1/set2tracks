from dotenv import load_dotenv
import os
load_dotenv()

SIGNUP_OPTIONS = {
    'allow_site': True,
    'allow_google': True,
    'allow_invite': True,
}

class Config:
    SQLALCHEMY_DATABASE_URI = DATABASE_URL = f"postgresql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    SECRET_KEY = os.environ.get('SECRET_KEY') 
    DB_TABLE_USERS = os.environ.get('DB_TABLE_USERS')
    DB_TABLE_INVITES = os.environ.get('DB_TABLE_INVITES')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    PWD_SALT_LENGTH = int(os.environ.get('PWD_SALT_LENGTH'))
    PWD_HASH_METHOD = os.environ.get('PWD_HASH_METHOD')
    LANGUAGES = ['en', 'es','fr']
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    SIGNUP_OPTIONS = SIGNUP_OPTIONS
    

    
