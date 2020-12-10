# redteam

Red Team simulation

## Components

- Postgres database
- Metasploit RPC api
- Python director




## Requirements

1. Install docker and docker-compose




## Usage

1. Make sure the metasploit volume has the right file permissions: `sudo chown -R 1201:1201 src/data/msf/`
1. Start the services: `docker-compose up --build -t 2`
1. (Probably something else needed here)
