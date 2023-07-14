#!/bin/sh

DIR=$(dirname "$0")
export MODE=production
export PORT=3000

# Change directory to project directory
cd $DIR 

# Terminate existing Gunicorn process
pkill -f "$DIR/venv/bin/gunicorn -w 4 -b 0.0.0.0:$PORT app:app"

#Run the application
$DIR/venv/bin/gunicorn -w 4 -b 0.0.0.0:$PORT app:app

