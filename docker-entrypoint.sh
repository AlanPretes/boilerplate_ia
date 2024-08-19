#!bin/sh

echo "Starting service..."

echo "Running migrations..."
flask db migrate
flask db upgrade

echo "Starting server..."
gunicorn "src:create_app()" --keep-alive 120 --bind 0.0.0.0:8000 --workers 4 --threads 8
