#!/bin/sh

# Check if the database is postgresql, and if so, wait for it to be ready
if [ "$DATABASE" = "test_health_before" ]
then
  echo "Waiting for postgres..."
  nc -z postgres 5432
  while ! nc -z postgres 5432; do
    sleep 0.1
  done

  echo "PostgreSQL started"
fi

#python -u -m director

exec "$@"