import pwd
import grp

passwords = {}

def group_finder(userid, request):
    try:
        pwd.getpwnam(userid)
    except KeyError:
        return None
    return [i.gr_name for i in grp.getgrall() if userid in i.gr_mem]