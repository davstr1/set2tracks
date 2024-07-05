from sqlalchemy import MetaData
from boilersaas.utils.db import db
from web import create_app

def reset_database():
    app = create_app()
    with app.app_context():
        # Drop all tables in the database
        print("Dropping all tables...")
        db.drop_all()
        print("All tables dropped.")
        
        # Recreate all tables in the database
        print("Recreating all tables...")
        db.create_all()
        print("All tables recreated.")

if __name__ == '__main__':
    reset_database()