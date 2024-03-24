#!/bin/bash

# Check if setup has already been done.
if [ -f "./web/app/static/css/output.css" ]; then
    echo "Setup has already been completed. Exiting..."
    exit 0
fi

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

# Check if .env file exists, if not, copy from example.env
if [ ! -f "./web/.env" ]; then
    echo "No .env file found in the web directory. Creating one from example.env..."
    cp "./web/example.env" "./web/.env"
    echo "A new .env file has been created from example.env. Please make sure to fill it out before running the application."
fi



echo "Installing npm packages..."
npm install tailwindcss

echo "Running Tailwind CSS build and watching for changes..."
npx tailwindcss -i ./web/static/css/input.css -o ./web/static/css/output.css --watch &

if [ "$1" == "dev" ]; then
    echo "Installing Python development dependencies..."
    pip install -r web/requirements_dev.txt
    pip install -e ./boilersaas
else
    echo "Installing Python production dependencies..."
    pip install -r web/requirements.txt
    echo "Removing ./boilerplate directory..."
    rm -rf ./boilerplate
fi

echo "Setup completed successfully!"
echo "Please ensure the .env file in the web directory is filled out before running the application."
