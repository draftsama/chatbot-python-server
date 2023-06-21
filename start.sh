#!/bin/sh
DIR=$(dirname "$0")

CERT_FILE=/home/ubuntu/ssl_certificate/certificate.pem
KEY_FILE=/home/ubuntu/ssl_certificate/privatekey.pem
export MODE=production
export OPENAI_API_KEY=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
$DIR/venv/bin/gunicorn --bind 0.0.0.0:5000 --certfile=$CERT_FILE --keyfile=$KEY_FILE app:app

