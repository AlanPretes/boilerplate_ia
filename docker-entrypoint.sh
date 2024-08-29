#!/bin/sh

set -e  # Faz o script parar em caso de erro

echo "Starting service..."

echo "Running makemigrations..."
python manage.py makemigrations || { echo 'Makemigrations failed' ; exit 1; }

echo "Running migrate..."
python manage.py migrate || { echo 'Migration failed' ; exit 1; }

echo "Creating superuser..."
python manage.py shell << END
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = 'autovist@@@@2024'
password = '2024@@@@autovist'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email='', password=password)
    print("Superuser created successfully.")
else:
    print("Superuser already exists.")
END

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000
