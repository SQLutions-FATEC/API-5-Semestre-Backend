#!/bin/bash
set -e

echo "Applying database migrations..."
python manage.py makemigrations
python manage.py migrate

if [ "$RUN_SEED" = "true" ] || [ "$RUN_SEED" = "True" ] || [ "$RUN_SEED" = "1" ]; then
    echo "Running dynamic seed with 2 programs and 5 projects..."
    python manage.py seed_dynamic --clear --programs=2 --projects=5
fi

echo "Starting server..."
exec "$@"
