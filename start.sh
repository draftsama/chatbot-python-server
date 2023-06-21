#!/bin/sh
DIR=$(dirname "$0")

CERT_FILE=/home/ubuntu/ssl_certificate/certificate.pem
KEY_FILE=/home/ubuntu/ssl_certificate/privatekey.pem
$DIR/venv/bin/gunicorn --bind 0.0.0.0:5000 --certfile=$CERT_FILE --keyfile=$KEY_FILE app:app

