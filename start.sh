#!/bin/bash
set -e  # Exit on any error

echo "🚀 Starting Invoice Generator..."

# Wait for DB if Postgres (optional)
if [ "$DATABASE_ENGINE" = "django.db.backends.postgresql" ] || [ "$DATABASE_ENGINE" = "postgresql" ]; then
    echo "⏳ Waiting for PostgreSQL (max 30s)..."
    for i in {1..30}; do
        if python -c "import psycopg; print('DB ready')" 2>/dev/null; then
            echo "✅ PostgreSQL ready!"
            break
        fi
        sleep 1
    done || echo "⚠️  No wait needed or timeout"
fi

# Run migrations
echo "📦 Running Django migrations..."
python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if needed (dev only)
if [ "$CREATE_SUPERUSER" = "true" ]; then
    echo "👤 Creating superuser..."
    SUPERUSER_EMAIL="${SUPERUSER_EMAIL:-admin@example.com}"
    SUPERUSER_PASSWORD="${SUPERUSER_PASSWORD:-admin123}"
    SUPERUSER_USERNAME="${SUPERUSER_USERNAME:-admin}"
    
    echo "   Email: $SUPERUSER_EMAIL"
    echo "   Username: $SUPERUSER_USERNAME"
    echo "   Password: $SUPERUSER_PASSWORD"
    
    # Use echo for password (secure input)
    python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$SUPERUSER_USERNAME').exists():
    User.objects.create_superuser(
        username='$SUPERUSER_USERNAME',
        email='$SUPERUSER_EMAIL',
        password='$SUPERUSER_PASSWORD'
    )
    print("✅ Superuser created!")
else:
    print("ℹ️  Superuser already exists")
EOF
fi

# Start ASGI server
echo "🌐 Starting uvicorn server..."
exec uvicorn invoice_generator.asgi:application \
    --host 0.0.0.0 \
    --port 8000 

