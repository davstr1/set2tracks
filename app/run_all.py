import subprocess

# Start the foreground process (blocking)
foreground_process = subprocess.Popen("python run.py", shell=True)

# Start background processes (non-blocking)
background_scripts = [
    "python cron_check_channels.py",
    "python cron_remove_temp_downloads.py",
    "python cron_set_insert.py",
    "python cron_set_queue.py"
]

background_processes = [
    subprocess.Popen(script, shell=True) for script in background_scripts
]

try:
    # Wait indefinitely for the foreground process
    foreground_process.wait()
except KeyboardInterrupt:
    # Handle shutdown signal (e.g., Ctrl+C)
    print("Shutting down...")
    for process in background_processes:
        process.terminate()
    foreground_process.terminate()
