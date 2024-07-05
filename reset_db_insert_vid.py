from pprint import pprint
from sqlalchemy import MetaData
from boilersaas.utils.db import db
from web import create_app
from web.controller import insert_set
from web.lib.youtube import youbube_video_info


def reset_database_and_insert_set():
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
        video_info = youbube_video_info('0mlnJ7Ic7TM')
        pprint(video_info)
        res = insert_set(video_info,delete_temp_files=False)
        pprint(res)

if __name__ == '__main__':
    reset_database_and_insert_set()
   