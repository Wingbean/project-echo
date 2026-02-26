# Gunicorn Configuration for Project Echo

# Server socket
bind = "0.0.0.0:5009"

# Worker processes
workers = 4
worker_class = "sync"
threads = 2

# Timeout (seconds) - generous for long-running SQL queries
timeout = 600
graceful_timeout = 120

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "project_echo"

# Server mechanics
preload_app = False
reload = False
