from pyramid.security import (
    Allow,
    Authenticated,
    )

class RootFactory(object):
    __acl__ = [ (Allow, Authenticated, 'view_site'),
                (Allow, 'group:editors', 'edit') ]
    
    def __init__(self, request):
        pass

