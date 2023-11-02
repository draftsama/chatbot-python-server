#!/bin/sh

DIR=$(dirname "$0")

export MODE=production
export PORT=3000
export SSL_CERT_DIR=/etc/ssl/certs

# Change directory to project directory
cd $DIR 

# Terminate existing Gunicorn process
pkill -f "$DIR/venv/bin/gunicorn -w 2 -b 0.0.0.0:$PORT app:app --worker-class gevent"

# Activate the virtual environment

#Run the application
$DIR/venv/bin/gunicorn -w 2 -b 0.0.0.0:$PORT app:app --worker-class gevent

