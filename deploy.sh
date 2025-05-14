#!/bin/bash

# Load environment variables
set -a
source .env.prod
set +a

# Pull latest changes
git pull origin main

# Build and start containers with Podman
podman-compose down
podman-compose build
podman-compose up -d

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 10

# Run migrations
podman-compose exec web python manage.py migrate

# Collect static files
podman-compose exec web python manage.py collectstatic --noinput

echo "Production deployment is complete!"
echo "Access the application at https://cockpitdash.com/folder"
