#!/bin/sh

export OPENAI_API_KEY=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
DIR=$(dirname "$0")
export MODE=production
export PORT=5000


# Change directory to project directory
cd $DIR 

# Terminate existing Gunicorn process
pkill -f "$DIR/venv/bin/gunicorn -w 4 -b 0.0.0.0:$PORT app:app"

#Run the application
$DIR/venv/bin/gunicorn -w 4 -b 0.0.0.0:$PORT app:app

