#!/bin/sh

# Check if the database is postgresql, and if so, wait for it to be ready
if [ "$CHECK_DB" = "1" ]
then
  echo "Waiting for postgres..."
  while ! nc -z "$DATABASE_HOST" "$DATABASE_PORT"; do
    sleep 0.1
  done

  echo "PostgreSQL started"
fi

python ttp/exploitation/test.py

exec "$@"