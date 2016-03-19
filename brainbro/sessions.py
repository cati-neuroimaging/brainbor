import os
import signal
import os.path as osp
import json
import paramiko

from brainbro.users_and_groups import passwords

sessions_base_port = 7000

def read_sessions_file():
    sessions_file = '/tmp/brainbro_sessions.json'
    if osp.exists(sessions_file):
        sessions = json.load(open(sessions_file))
    else:
        sessions = {}
    return sessions

def write_sessions_file(sessions):
    sessions_file = '/tmp/brainbro_sessions.json'
    if sessions:
        json.dump(sessions, open(sessions_file,'w'), indent=2)
    else:
        if osp.exists(sessions_file):
            os.remove(sessions_file)


def create_session(login):
    sessions = read_sessions_file()
    for session_number in range(100):
        if str(session_number) not in sessions:
            break
    else:
        raise ValueError('Too many sessions')
    
    port = sessions_base_port + session_number
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('127.0.0.1', username=login, password=passwords[login])
    command = 'nohup ~/fake_session/bin/python ~/fake_session/bin/waitress-serve --port %d fake_session:main > /dev/null 2>&1 & echo $!'
    command = osp.expanduser(command)
    stdin, stdout, stderr = ssh.exec_command(command % port)
    pid = stdout.read().strip()
    sessions[str(session_number)] = {
        'number': session_number,
        'pid': pid,
        'url': 'http://127.0.0.1:%d' % port,
        'login': login,
    }
    write_sessions_file(sessions)
    return session_number


def destroy_session(session_number):
    sessions = read_sessions_file()
    session = sessions.pop(str(session_number), None)
    if session is not None:
        login = session['login']
        password = passwords[login]
        pid = session['pid']
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('127.0.0.1', username=login, password=password)
        ssh.exec_command('kill %s' % pid)
        write_sessions_file(sessions)
    else:
        raise ValueError('Session {0} does not exist'.format(session_number))

def get_user_sessions(login):
    sessions = read_sessions_file()
    return [s for s in sessions.itervalues() if s['login'] == login]
