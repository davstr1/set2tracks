from app import create_app
import os, glob

app = create_app()

# Define the path to your templates directory
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
# Use glob to list all files within the templates directory
template_files = glob.glob(template_dir + '/**/*.html', recursive=True)

if __name__ == '__main__':
    app.run(debug=True,extra_files=template_files,use_reloader=True)
     
        
    

