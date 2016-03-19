# -*- coding: utf-8 -*-

from uuid import uuid4

from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from brainbro.users_and_groups import group_finder


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    authn_policy = AuthTktAuthenticationPolicy(
        str(uuid4()), callback=group_finder, hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()
    config = Configurator(settings=settings,
                          root_factory='brainbro.models.RootFactory')
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.include('pyramid_jinja2')
    config.add_static_view('static', path='static', cache_max_age=3600)
    
    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')

    config.add_route('create_session', '/session/create')
    config.add_route('destroy_session', '/session/destroy/{session}')
    
    config.scan()
    return config.make_wsgi_app()
