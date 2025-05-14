#!/bin/bash

# Check if PostgreSQL is ready
postgres_ready() {
    python << END
import sys
import psycopg2
try:
    psycopg2.connect(
        dbname="${POSTGRES_DB}",
        user="${POSTGRES_USER}",
        password="${POSTGRES_PASSWORD}",
        host="${DB_HOST}",
        port="${DB_PORT:-5432}",
    )
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}

# Check if Redis is ready
redis_ready() {
    python << END
import sys
import redis
try:
    redis.Redis.from_url("${REDIS_URL}").ping()
except redis.exceptions.ConnectionError:
    sys.exit(-1)
sys.exit(0)
END
}

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
until postgres_ready; do
  sleep 1
done
echo "PostgreSQL started"

# Wait for Redis
echo "Waiting for Redis..."
until redis_ready; do
  sleep 1
done
echo "Redis started"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Create superuser if needed
echo "Creating superuser..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='alideals.co.uk@gmail.com').exists():
    User.objects.create_superuser('alideals.co.uk@gmail.com', 'alideals.co.uk@gmail.com', 'Admin255255@@')
END

# Build Tailwind CSS
echo "Building Tailwind CSS..."
npm run build:css

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Celery worker in background
celery -A taskmanager worker --loglevel=info &

# Start Celery beat in background
celery -A taskmanager beat --loglevel=info &

# Start Celery flower in background
celery -A taskmanager flower --port=5555 &

# Start server
echo "Starting server..."
exec "$@"
