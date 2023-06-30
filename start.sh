#!/bin/sh

export OPENAI_API_KEY=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

# DIR=$(dirname "$0")

export MODE=production
$DIR/venv/bin/gunicorn -w 4 -b 0.0.0.0:3000 app:app


