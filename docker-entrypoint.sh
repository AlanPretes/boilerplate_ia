#!/bin/sh

set -e

echo "Starting service..."

echo "Running makemigrations..."
python manage.py makemigrations || { echo 'Makemigrations failed' ; exit 1; }

echo "Running migrate..."
python manage.py migrate || { echo 'Migration failed' ; exit 1; }

echo "Starting server..."
gunicorn \
    --workers 6 \
    --threads 8 \
    --max-requests 80000 \
    --timeout 120 \
    --keep-alive 5 \
    config.wsgi:application \
    --bind 0.0.0.0:8000
