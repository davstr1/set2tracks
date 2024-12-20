import subprocess

# List of scripts to run
scripts = [
    "python run.py",
    "python cron_check_channels.py",
    "python cron_remove_temp_downloads.py",
    "python cron_set_insert.py",
    "python cron_set_queue.py"
]

# Start all scripts in parallel (non-blocking)
processes = [subprocess.Popen(script, shell=True) for script in scripts]

# Optionally print process details or log them
for process, script in zip(processes, scripts):
    print(f"Started {script} with PID {process.pid}")
