from pyramid.view import view_config

from pyramid.httpexceptions import (
    HTTPFound,
    )

from pyramid.view import (
    view_config,
    forbidden_view_config,
    )

from pyramid.security import (
    remember,
    forget,
    )

import paramiko

from brainbro.users_and_groups import passwords
from brainbro.sessions import SessionsManager

_sessions_manager = None
def get_sessions_manager():
    global _sessions_manager
    if _sessions_manager is None:
        _sessions_manager = SessionsManager()
    return _sessions_manager

@view_config(route_name='login', renderer='templates/login.jinja2')
@forbidden_view_config(renderer='templates/login.jinja2')
def login(request):
    login_url = request.route_url('login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/' # never use the login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    message = ''
    login = ''
    password = ''
    if 'form.submitted' in request.params:
        login = request.params['login']
        password = request.params['password']
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect('127.0.0.1', username=login, password=password)
            headers = remember(request, login)
            passwords[login] = password
            return HTTPFound(location = came_from,
                             headers = headers)
        except paramiko.AuthenticationException:
            message = 'Failed login'

    return dict(
        message = message,
        url = request.application_url + '/login',
        came_from = came_from,
        login = login,
        password = password,
        )


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location = request.route_url('home'),
                     headers = headers)


@view_config(route_name='home', renderer='templates/home.jinja2', permission='view_site')
def home(request):
    sessions_manager = get_sessions_manager()
    return {'sessions': sessions_manager.get_user_sessions(request.authenticated_userid)}

@view_config(route_name='create_session', permission='view_site')
def create_session_view(request):
    sessions_manager = get_sessions_manager()
    sessions_manager.create_session(request.authenticated_userid)
    return HTTPFound(location = request.route_url('home'))

@view_config(route_name='destroy_session', permission='view_site')
def destroy_session_view(request):
    number = int(request.matchdict['session'])
    sessions_manager = get_sessions_manager()
    sessions_manager.destroy_session(number)
    return HTTPFound(location = request.route_url('home'))

