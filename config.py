from re import A
from dotenv import load_dotenv
import os,sys
load_dotenv()

SIGNUP_OPTIONS = {
    'allow_site': True,
    'allow_google': True,
    'allow_invite': True,
}

class Config:
    try:
        EXPLAIN_TEMPLATE_LOADING = False # Suppress detailed template loading messages
        SQLALCHEMY_DATABASE_URI = f"postgresql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
        SECRET_KEY = os.environ['SECRET_KEY'] 
        DB_TABLE_USERS = os.environ['DB_TABLE_USERS']
        DB_TABLE_INVITES = os.environ['DB_TABLE_INVITES']
        PWD_SALT_LENGTH = int(os.environ['PWD_SALT_LENGTH'])
        PWD_HASH_METHOD = os.environ['PWD_HASH_METHOD']
        LANGUAGES = ['en', 'es', 'fr']
        MAIL_SERVER = os.environ['MAIL_SERVER']
        MAIL_PORT = os.environ['MAIL_PORT']
        MAIL_USE_TLS = os.environ['MAIL_USE_TLS']
        MAIL_USERNAME = os.environ['MAIL_USERNAME']
        MAIL_PASSWORD = os.environ['MAIL_PASSWORD']
        MAIL_DEFAULT_SENDER = os.environ['MAIL_DEFAULT_SENDER']
        GOOGLE_CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']
        GOOGLE_CLIENT_SECRET = os.environ['GOOGLE_CLIENT_SECRET']
        SIGNUP_OPTIONS = SIGNUP_OPTIONS
        LOGGING_CONFIG_FILE = os.environ['LOGGING_CONFIG_FILE']
        ADMIN_UID = os.environ['ADMIN_UID']
        NOTIF_SOUND = 'pop-bouncy-plop-betacut-1-00-02.mp3'
    except KeyError as e:
        sys.exit(f"Missing environment variable(s). Please add all the required environments variables as instructed in the README")
    

    
