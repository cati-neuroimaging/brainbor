import os

sessions_base_port = 7000

def main(environ, start_response):
    '''This function is a WSGI application that can be used to create
    a minimal web server with the following command :
    
    waitress-serve --port=6544 sessions_manager.sessions:fake_session
    '''
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    session_number = int(environ['SERVER_PORT']) - sessions_base_port
    return ['This is session number {0} for {1}'.format(session_number, os.getlogin())]
