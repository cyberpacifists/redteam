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

1. Start the database: `docker-compose -f docker-compose-db.yml up -t 2`
   (persistence is disabled, removing the container will reset the data)
1. Start director and workers: `docker-compose -f docker-compose-workers.yml up -t 2`
1. Start the director: `docker-compose up --build -t 2`


If you want to debug the state of the database or perform 
manual actions in metasploit, you can connect to the
msfconsole by `docker attach redteam_msfconsole_1`


## Development

- hack into director directory
