def get_locale():
  print('getting locale and the result is es')
  return 'es'
   # return request.accept_languages.best_match(Config['LANGUAGES'])
   
   
def add_babel_translation_directory(new_dir,app):
    
    # Check if 'BABEL_TRANSLATION_DIRECTORIES' exists in app.config
    if 'BABEL_TRANSLATION_DIRECTORIES' in app.config:
        # Split the current value into a list, remove empty entries
        current_dirs = [d for d in app.config['BABEL_TRANSLATION_DIRECTORIES'].split(';') if d]
        # Add the new directory if it's not already in the list
       
        if new_dir not in current_dirs:
            current_dirs.append(new_dir)
        # Update the app.config with the new semi-colon separated string
        app.config['BABEL_TRANSLATION_DIRECTORIES'] = ';'.join(current_dirs)
    else:
        # If it doesn't exist, set it to the new directory
        app.config['BABEL_TRANSLATION_DIRECTORIES'] = new_dir