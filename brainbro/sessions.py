import os
import signal
import os.path as osp
import json
import subprocess
import paramiko
import xml.etree.cElementTree as ET
import uuid
import socket

from brainbro.users_and_groups import passwords

class SessionsManager(object):
    sessions_max = 100
    sessions_base_port = 5901
    default_directory = '/tmp/brainbro'
    guacamole_user_xml = '''
    <authorize username="{0}" password="{1}">
        <protocol>vnc</protocol>
        <param name="hostname">localhost</param>
        <param name="port">{2}</param>
        <param name="password">{3}</param>
    </authorize>'''
    vnc_xstartup = '''#!/bin/sh

xrdb $HOME/.Xresources
xsetroot -solid grey
#x-terminal-emulator -geometry 80x24+10+10 -ls -title "$VNCDESKTOP Desktop" &
#x-window-manager &
# Fix to make GNOME work
export XKL_XMODMAP_DISABLE=1
#/etc/X11/Xsession

/i2bm/brainvisa/Ubuntu-14.04-x86_64/brainvisa/bin/bv_env anasimpleviewer.py -i /neurospin/lnao/Panabase/data/diffusion/caca/t1mri/default_acquisition/default_analysis/nobias_caca.ima
'''
    
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
        user_password = passwords[login]
        vnc_password = 'gabuzome' # shoul be str(uuid.uuid4())
        encoded_vnc_password = 'k\xe1\xf7\xdfQ{"\x02'
    
        guacamole_user_mapping = osp.join(osp.dirname(__file__), '..', '..', 'user-mapping.xml')
        tree = ET.parse(guacamole_user_mapping)
        xml = tree.getroot()
        for authorize in xml:
            if authorize.get('username') == login:
                break
        else:
            # Add user to guacamole file
            new = ET.fromstring(self.guacamole_user_xml.format(login, user_password, port, vnc_password))
            xml.append(new)
            tree.write(guacamole_user_mapping)
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('127.0.0.1', username=login, password=user_password, allow_agent=False)
    
        sftp = ssh.open_sftp()
        try:
            sftp.mkdir('.vnc')
        except IOError:
            pass
        file = sftp.open('.vnc/passwd', 'w')
        file.write(encoded_vnc_password)
        file.close()
        sftp.chmod('.vnc/passwd', 0600)
        file = sftp.open('.vnc/xstartup', 'w')
        file.write(self.vnc_xstartup)
        file.close()
        sftp.chmod('.vnc/xstartup', 0770)
 
        ssh.exec_command('bash -l -c "env" > /tmp/env')
        #command = 'Xtightvnc :1 -desktop X -httpd /usr/share/tightvnc-java -auth /tmp/blublu -geometry 1024x768 -depth 24 -rfbwait 120000 -rfbauth /home/yc176684/.vnc/passwd -rfbport 5901 -fp /usr/share/fonts/X11/misc/,/usr/share/fonts/X11/Type1/usr/share/fonts/X11/75dpi/,/usr/share/fonts/X11/100dpi/ -co /etc/X11/rgb'
        command = 'tightvncserver -nevershared -geometry 1024x768 :{0}'.format(session_number + 1)
        i, o, e = ssh.exec_command('bash -l -c "%s"' % command)
        open('/tmp/stdout', 'w').write(o.read())
        open('/tmp/stderr', 'w').write(e.read())
        sessions[str(session_number)] = {
            'number': session_number,
            'url': 'http://%s:8080/guacamole' % socket.gethostname(),
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
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect('127.0.0.1', username=login, password=password, allow_agent=False)
            i, o, e = ssh.exec_command('tightvncserver -kill :{0}'.format(session_number + 1))
            open('/tmp/stdout', 'w').write(o.read())
            open('/tmp/stderr', 'w').write(e.read())            
            guacamole_user_mapping = osp.join(osp.dirname(__file__), '..', '..', 'user-mapping.xml')
            tree = ET.parse(guacamole_user_mapping)
            xml = tree.getroot()
            for authorize in xml:
                if authorize.get('username') == login:
                    # Add user to guacamole file
                    xml.remove(authorize)
                    tree.write(guacamole_user_mapping)
                    break            
            self.write_sessions_file(sessions)
        else:
            raise ValueError('Session {0} does not exist'.format(session_number))

    def get_user_sessions(self, login):
        sessions = self.read_sessions_file()
        return [s for s in sessions.itervalues() if s['login'] == login]
