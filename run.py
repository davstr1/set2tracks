import logging
from pdb import run
import time
from web import create_app
import os, glob



app = create_app()

# Define the path to your templates directory
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
# Use glob to list all files within the templates directory
template_files = glob.glob(template_dir + '/**/*.html', recursive=True)

def run_app():
    app.run(debug=True, port=50001, extra_files=template_files, use_reloader=True)
        
    
if __name__ == '__main__':
        run_app()