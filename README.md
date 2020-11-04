# redteam

Red Team simulation

## Requirements

1. Install docker and docker-compose


## Components

- Postgres database
- Vulnerable hosts:
  - Apache httpd vulnerable to shellshock
  - DVWA (Damn Vulnerable Web Application)
- Metasploit RPC api (red team worker)
- Python director (red team director)
- Metasploit console (for debugging)


## Usage

### First start the database

1. Run `docker-compose -f docker-compose-db.yml up --build -t 2`
 
(persistence is disabled, removing the container will reset the data)

### Start director and workers

1. Run `docker-compose up --build -t 2`

If you want to debug the state of the database or perform 
manual actions in metasploit, you can connect to the
msfconsole by `docker attach redteam_msfconsole_1`


## Development

- hack into director directory
