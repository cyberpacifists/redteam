sh -c "echo 'production:
  adapter: postgresql
  database: $DATABASE_DB
  username: $DATABASE_USER
  password: $DATABASE_PASSWORD
  host: localhost
  port:
  pool: 200
  timeout: 5'  > /usr/share/metasploit-framework/config/database.yml"

