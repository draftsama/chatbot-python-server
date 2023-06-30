#!/bin/sh

export OPENAI_API_KEY=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
DIR=$(dirname "$0")
export MODE=production

# Change directory to project directory
cd $DIR 

# Terminate existing Gunicorn process
pkill -f "$DIR/venv/bin/gunicorn -w 4 -b 0.0.0.0:$PORT app:app"

#Run the application
$DIR/venv/bin/gunicorn -w 4 -b 0.0.0.0:$PORT app:app

