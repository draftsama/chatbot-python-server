#!/bin/sh

export OPENAI_API_KEY=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

# DIR=$(dirname "$0")

# CERT_FILE=/home/ubuntu/ssl_certificate/certificate.pem
# KEY_FILE=/home/ubuntu/ssl_certificate/privatekey.pem
# export MODE=production
# $DIR/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 --certfile=$CERT_FILE --keyfile=$KEY_FILE app:app


#on deploy to render server
gunicorn -w 4 -b 0.0.0.0:5000 app:app
