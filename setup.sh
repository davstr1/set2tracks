#!/bin/bash

# # Check if setup has already been done.
# if [ -f "./web/static/css/tailwind/output.css" ]; then
#     echo "Setup has already been completed. Exiting..."
#     exit 0
# fi

echo "Starting app setup..."

# Initialize variable to keep track of missing commands
missing_cmds=""

# Check if npm is available
if ! command -v npm &> /dev/null; then
    missing_cmds+="npm "
fi

# Check if npx is available
if ! command -v npx &> /dev/null; then
    missing_cmds+="npx "
fi

# Check if python is available
if ! command -v python &> /dev/null; then
    missing_cmds+="python "
fi

# If any commands are missing, display them and exit
if [ ! -z "$missing_cmds" ]; then
    echo "The following commands are missing, please install them before proceeding: $missing_cmds"
    exit 1
fi

if [ "$1" == "dev" ]; then
    echo "Installing Python development dependencies..."
    pip install -r requirements_dev.txt
    pip install -e ./boilersaas
else
    echo "Installing Python production dependencies..."
    pip install -r requirements.txt
    
fi

echo "Installing npm packages..."
npm install


INIT_RESSOURCES_DIR="boilersaas/src/boilersaas/init_ressources"

# Check if the 'dev' argument is provided
if [ "$1" != "dev" ]; then
    # No 'dev' argument provided, proceed with overwriting .gitignore
    echo "No 'dev' argument given. Overwriting .gitignore with .gitignore_regular..."
    
    # Overwrite .gitignore with .gitignore_regular
    cp "${INIT_RESOURCES_DIR}/.gitignore_regular" ./.gitignore
    
    # Confirm the operation
    if [ $? -eq 0 ]; then
        echo ".gitignore has been updated successfully."
    else
        echo "Error updating .gitignore. Please check your paths and permissions."
    fi
else
    # 'dev' argument provided, do not overwrite .gitignore
    echo "'dev' argument given. No changes made to .gitignore."
fi


echo "Getting default_templates..."

# Define source and destination directories
TEMPLATES_SRC_DIR="boilersaas/src/boilersaas/templates"
TEMPLATES_DEFAULTS_DIR="templates_defaults"

# Check if the destination directory exists
if [ -d "$TEMPLATES_DEFAULTS_DIR" ]; then
    # Find all files and directories within TEMPLATES_DEFAULTS_DIR except for README.md
    find "$TEMPLATES_DEFAULTS_DIR" -mindepth 1 -not -name 'README.md' | while read line; do
        # Check if it's a directory or a file and delete accordingly
        if [ -d "$line" ]; then
            rm -rf "$line"
        else
            rm -f "$line"
        fi
    done
else
    # If the destination directory doesn't exist, create it
    mkdir "$TEMPLATES_DEFAULTS_DIR"
fi

# Copy the source directory content to the destination
cp -R "$TEMPLATES_SRC_DIR/" "$TEMPLATES_DEFAULTS_DIR/"


WEB_TEMPLATES_DIR="web/templates"
echo "Checking for $WEB_TEMPLATES_DIR directory..."

# Attempt to create the web/templates directory. Proceed with additional operations only if it didn't exist and has been created.
if mkdir -p "$WEB_TEMPLATES_DIR" && [ "$(ls -A "$WEB_TEMPLATES_DIR")" ]; then
    echo "$WEB_TEMPLATES_DIR already exists and is not empty."
else
    echo "$WEB_TEMPLATES_DIR did not exist or was empty. Setting up templates starter kit..."

    # Since the templates directory was just created or was empty, copy the mail directory and logo.html

    # Check and copy mail directory if it doesn't exist in web/templates
    if [ ! -d "$WEB_TEMPLATES_DIR/email" ]; then
        cp -R "$TEMPLATES_SRC_DIR/email" "$WEB_TEMPLATES_DIR/"
        echo "Copied mail directory to $WEB_TEMPLATES_DIR."
    fi

    # Check and copy logo.html if it doesn't exist in web/templates
    if [ ! -f "$WEB_TEMPLATES_DIR/logo.html" ]; then
        cp "$TEMPLATES_SRC_DIR/logo.html" "$WEB_TEMPLATES_DIR/"
        echo "Copied logo.html to $WEB_TEMPLATES_DIR."
    fi
fi

WEB_CSS_DIR="web/static/css"
# Check if custom.css exists or create it if it doesn't
if [ ! -f "$WEB_CSS_DIR/tailwind/custom.css" ]; then
    mkdir -p "$WEB_CSS_DIR/tailwind" # Ensure the directory exists
    touch "$WEB_CSS_DIR/tailwind/custom.css" # Create the file
    echo "Created $WEB_CSS_DIR/tailwind/custom.css."
else
    echo "$WEB_CSS_DIR/tailwind/custom.css already exists."
fi

# Check if tailwind.config.custom.js doesn't exist and create it in the current directory
if [ ! -f "./tailwind.config.custom.js" ]; then
    touch "./tailwind.config.custom.js" # Create the file
    echo "Created tailwind.config.custom.js in the current directory."
else
    echo "tailwind.config.custom.js already exists in the current directory."
fi


ROUTES_SRC_FILE="init_ressources/example_routes.py"
ROUTES_DEST_FILE="web/routes.py"
echo "Getting basic web/routes.py"
# Check if web/routes.py exists, if not, copy from example_routes.py
if [ ! -f "$ROUTES_DEST_FILE" ]; then
    cp "$ROUTES_SRC_FILE" "$ROUTES_DEST_FILE"
fi

# Check if .env file exists, if not, copy from example.env
if [ ! -f ".env" ]; then
    echo "No .env file found in the web directory. Creating one from example.env..."
    cp "init_ressources/.example.env" ".env"
    echo "A new .env file has been created from example.env. Please make sure to fill it out before running the application."
fi




# echo "Running Tailwind CSS build and watching for changes..."
# npx tailwindcss -i ./web/static/css/tailwind/input.css -o ./web/static/css/tailwind/output.css --watch &

echo "Setup completed successfully!"
echo "Please ensure the .env file in the web directory is filled out before running the application."
