#!/bin/bash
set -e

echo "Applying database migrations..."
python manage.py makemigrations
python manage.py migrate

if [[ "$RUN_SEED" = "true" ]] || [[ "$RUN_SEED" = "True" ]] || [[ "$RUN_SEED" = "1" ]]; then
    echo "Checking if database is empty..."
    if python manage.py shell -c "import sys; from api.models import DimPrograma; sys.exit(1 if DimPrograma.objects.exists() else 0)"; then
        echo "Database is empty. Running dynamic seed with 2 programs and 5 projects..."
        python manage.py seed_dynamic --programs=2 --projects=5
    else
        echo "Database is not empty. Skipping seed."
    fi
fi

echo "Starting server..."
exec "$@"
