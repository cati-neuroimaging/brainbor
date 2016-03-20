import os
import signal
import os.path as osp
import json
import subprocess
import paramiko

from brainbro.users_and_groups import passwords

class SessionsManager(object):
    sessions_max = 100
    sessions_base_port = 7000
    default_directory = '/tmp/brainbro'
    
    def __init__(self, directory=None):
        if directory is None:
            self.directory = self.default_directory
        else:
            self.directory = directory
        if not osp.exists(self.directory):
            os.mkdir(self.directory)
        venv = osp.join(self.directory, 'venv')
        if not osp.exists(venv):
            subprocess.check_call(['virtualenv', venv])
            pip = osp.join(venv, 'bin', 'pip')
            subprocess.check_call([pip, 'install', 'waitress'])
            os.symlink('../../../fake_session.py', osp.join(venv, 'lib', 'python2.7', 'site-packages', 'fake_session.py'))
        # Always copy fake_session.py in case sources are modified
        fake_session_src = osp.join(osp.dirname(__file__), 'fake_session.py')
        fake_session_dst = osp.join(venv, 'fake_session.py')
        open(fake_session_dst, 'w').write(open(fake_session_src).read())
        os.chmod(fake_session_dst, 0664)
        
    def read_sessions_file(self):
        sessions_file = osp.join(self.directory, 'sessions.json')
        if osp.exists(sessions_file):
            sessions = json.load(open(sessions_file))
        else:
            sessions = {}
        return sessions

    def write_sessions_file(self, sessions):
        sessions_file = osp.join(self.directory, 'sessions.json')
        if sessions:
            json.dump(sessions, open(sessions_file,'w'), indent=2)
        else:
            if osp.exists(sessions_file):
                os.remove(sessions_file)

    def create_session(self, login):
        sessions = self.read_sessions_file()
        for session_number in range(self.sessions_max):
            if str(session_number) not in sessions:
                break
        else:
            raise ValueError('Too many existing sessions')
    
        port = self.sessions_base_port + session_number
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('127.0.0.1', username=login, password=passwords[login])
        venv = osp.join(self.directory, 'venv')
        command = 'nohup {0}/bin/python {0}/bin/waitress-serve --port {1} fake_session:main > /dev/null 2>&1 & echo $!'.format(venv, port)
        stdin, stdout, stderr = ssh.exec_command(command)
        pid = stdout.read().strip()
        sessions[str(session_number)] = {
            'number': session_number,
            'pid': pid,
            'url': 'http://127.0.0.1:%d' % port,
            'login': login,
        }
        self.write_sessions_file(sessions)
        return session_number

    def destroy_session(self, session_number):
        sessions = self.read_sessions_file()
        session = sessions.pop(str(session_number), None)
        if session is not None:
            login = session['login']
            password = passwords[login]
            pid = session['pid']
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect('127.0.0.1', username=login, password=password)
            ssh.exec_command('kill %s' % pid)
            self.write_sessions_file(sessions)
        else:
            raise ValueError('Session {0} does not exist'.format(session_number))

    def get_user_sessions(self, login):
        sessions = self.read_sessions_file()
        return [s for s in sessions.itervalues() if s['login'] == login]
