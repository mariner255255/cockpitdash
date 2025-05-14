#!/bin/bash

# Load environment variables
set -a
source .env.dev
set +a

# Build and start containers
docker-compose down
docker-compose build
docker-compose up -d

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 10

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Create superuser if needed
docker-compose exec web python manage.py createsuperuser --noinput || true

echo "Development environment is ready!"
echo "Access the application at http://localhost:8000"
