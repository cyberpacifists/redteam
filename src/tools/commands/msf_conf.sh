metasploit() {
    docker run --rm -it -v "${HOME}/.msf4:/home/msf/.msf4" metasploitframework/metasploit-framework ./msfconsole "$@"
}

sh -c "echo 'production:
  adapter: postgresql
  database: $DATABASE_DB
  username: $DATABASE_USER
  password: $DATABASE_PASSWORD
  host: localhost
  port:
  pool: 200
  timeout: 5'  > /usr/share/metasploit-framework/config/database.yml"

