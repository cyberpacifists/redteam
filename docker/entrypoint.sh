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

# sleep for 10 seconds to give time to metasploit container to run
echo "Giving 10s metasploit to start..."
sleep 10
echo "Starting!"

python -m planner

exec "$@"