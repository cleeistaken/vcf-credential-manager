"""
Gunicorn Configuration for VCF Credentials Manager
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
# Start with 1 worker to avoid database initialization race conditions
# Can be increased after first run: workers = multiprocessing.cpu_count() * 2 + 1
workers = 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = 'logs/gunicorn_access.log'
errorlog = 'logs/gunicorn_error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'vcf_credentials_manager'

# Server mechanics
daemon = False
pidfile = 'gunicorn.pid'  # Store PID for restart functionality
umask = 0
user = None
group = None
tmp_upload_dir = None

# Preload app to initialize database before forking workers
preload_app = True

# macOS-specific: Disable fork safety for Objective-C frameworks
# This prevents crashes when fork() is called with Objective-C initialized
def pre_fork(server, worker):
    """Called just before a worker is forked"""
    import os
    os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

# SSL (only if using HTTPS directly with Gunicorn)
# Uncomment and configure these if you want Gunicorn to handle SSL
# keyfile = 'ssl/key.pem'
# certfile = 'ssl/cert.pem'
# ssl_version = 2  # TLS
# cert_reqs = 0    # No client cert required
# ca_certs = None
# suppress_ragged_eofs = True
# do_handshake_on_connect = False
# ciphers = None

# For production, use a reverse proxy (Nginx/Apache) for SSL
# and run Gunicorn on HTTP only

