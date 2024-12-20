import os

# Run the main application
os.system("python run.py")

# Run additional cron scripts sequentially
os.system("python cron_check_channels.py")
os.system("python cron_remove_temp_downloads.py")
os.system("python cron_set_insert.py")
os.system("python cron_set_queue.py")
