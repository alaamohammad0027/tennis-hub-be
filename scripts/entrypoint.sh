#!/bin/bash
set -e  # Exit on error

# Function to check command status
check_status() {
    if [ $? -eq 0 ]; then
        echo "✅ $1 completed successfully"
    else
        echo "❌ $1 failed"
        exit 1
    fi
}

# Set permissions for the /app directory
echo "Setting permissions..."
chmod -R 777 /app
check_status "Permission setting"

echo "Waiting for database to be ready..."
python /app/scripts/wait_for_db.py
check_status "Database check"

echo "Running migrations..."
python /app/manage.py migrate --fake-initial
check_status "Migrations"

# Run initial data loading for translations
echo "Updating translations..."
python /app/manage.py update_translation_fields
check_status "Translations"

echo "Collecting static files..."
python /app/manage.py collectstatic --noinput
check_status "Static files collection"

# Process translations
echo "Processing translations..."
if [ -d "/app/locale" ] && [ "$(find /app/locale -name '*.po' | wc -l)" -gt 0 ]; then
    cd /app && python manage.py compilemessages -v 2
    check_status "Translation compilation"
else
    echo "No translation files found, skipping compilation"
fi

echo "Starting Gunicorn..."
exec gunicorn project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 30 \
    --access-logfile - \
    --error-logfile - \
    --log-level info