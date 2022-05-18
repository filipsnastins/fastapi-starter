import os

bind = f"{os.getenv('HOST', '127.0.0.1')}:{os.getenv('PORT', '8000')}"

# Server Mechanics
worker_tmp_dir = "/dev/shm"  # nosec: B108

# Worker Processes
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 30
graceful_timeout = 30
