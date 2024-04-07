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

echo "Getting default_templates..."

# Define source and destination directories
SRC_DIR="boilersaas/src/boilersaas/templates"
DEST_DIR="templates_defaults"

# Check if the destination directory exists
if [ -d "$DEST_DIR" ]; then
    # Find all files and directories within DEST_DIR except for README.md
    find "$DEST_DIR" -mindepth 1 -not -name 'README.md' | while read line; do
        # Check if it's a directory or a file and delete accordingly
        if [ -d "$line" ]; then
            rm -rf "$line"
        else
            rm -f "$line"
        fi
    done
else
    # If the destination directory doesn't exist, create it
    mkdir "$DEST_DIR"
fi

# Copy the source directory content to the destination
cp -R "$SRC_DIR/" "$DEST_DIR/"


WEB_TEMPLATES_DIR="web/templates"
echo "Getting basic web/templates..."

# Check and copy mail directory if it doesn't exist in web/templates
if [ ! -d "$WEB_TEMPLATES_DIR/mail" ]; then
    cp -R "$SRC_DIR/mail" "$WEB_TEMPLATES_DIR/"
fi

# Check and copy logo.html if it doesn't exist in web/templates
if [ ! -f "$WEB_TEMPLATES_DIR/logo.html" ]; then
    cp "$SRC_DIR/logo.html" "$WEB_TEMPLATES_DIR/"
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

# echo "Running Tailwind CSS build and watching for changes..."
# npx tailwindcss -i ./web/static/css/tailwind/input.css -o ./web/static/css/tailwind/output.css --watch &

echo "Setup completed successfully!"
echo "Please ensure the .env file in the web directory is filled out before running the application."
