import os
import time
from web.logger import logger
from datetime import datetime, timedelta

# Path to the "temp_downloads" directory relative to the script location
TEMP_DOWNLOADS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_downloads")

# Time threshold for removing folders (1 day)
THRESHOLD = timedelta(days=1)

def get_folder_time(path):
    """
    Get the creation or modification time of a folder in a way that works
    for both macOS and Unix-like systems.
    """
    stat = os.stat(path)
    try:
        # macOS-specific: use st_birthtime if available
        return datetime.fromtimestamp(stat.st_birthtime)
    except AttributeError:
        # Fallback: use st_mtime (last modification time)
        return datetime.fromtimestamp(stat.st_mtime)

def remove_old_folders():
    try:
        now = datetime.now()
        for folder_name in os.listdir(TEMP_DOWNLOADS_PATH):
            folder_path = os.path.join(TEMP_DOWNLOADS_PATH, folder_name)

            # Check if it's a directory
            if os.path.isdir(folder_path):
                logger.info(f"Checking folder: {folder_path}")
                folder_time = get_folder_time(folder_path)
                time_difference = now - folder_time

                # If the folder is older than the threshold, remove it
                if time_difference > THRESHOLD:
                    logger.info(f"Removing folder {folder_path}, last modified/created {time_difference.days} days ago")
                    try:
                        # Remove the folder and its contents
                        for root, dirs, files in os.walk(folder_path, topdown=False):
                            for name in files:
                                os.remove(os.path.join(root, name))
                            for name in dirs:
                                os.rmdir(os.path.join(root, name))
                        os.rmdir(folder_path)

                        logger.info(f"Removed folder: {folder_path} (created/modified {time_difference.days} days ago)")
                    except Exception as e:
                        logger.error(f"Error removing folder {folder_path}: {e}")
    except Exception as e:
        logger.error(f"Error while scanning folders: {e}")

if __name__ == "__main__":
    while True:
        remove_old_folders()
        time.sleep(60)  # Wait for 1 minute before checking again
