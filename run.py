import logging
import time
from web import create_app
import os, glob



app = create_app()

# Define the path to your templates directory
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
# Use glob to list all files within the templates directory
template_files = glob.glob(template_dir + '/**/*.html', recursive=True)

def run_app():
    try:
        app.run(debug=True, port=50001, extra_files=template_files, use_reloader=True)
    except Exception as e:
        print(f"Error occurred: {e}. Restarting the application in 5 seconds...")
        time.sleep(5)
        run_app()

if __name__ == '__main__':
    while True:
        try:
            run_app()
        except Exception as e:
            print(f"Unhandled error: {e}. Restarting the application in 5 seconds...")
            time.sleep(5)