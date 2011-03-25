"""Define a bunch of functions that change request.fs.

These functions determine the handelability of a request, and run in the order
given here.

"""
import os
from os.path import join, isfile, isdir, dirname, exists

from aspen import Response


def translate(request, root):
    parts = [root] + request.path.raw.lstrip('/').split('/')
    request.fs = os.sep.join(parts).rstrip(os.sep)
    return parts

def check_sanity(request):
    """Make sure the request is under our root
    """
    if not request.fs.startswith(request.root):
        raise response(404)

def hidden_files(request):
    if '/.' in request.fs[len(request.root):]:
        raise Response(404)

def virtual_paths(request, parts):
    if not exists(request.fs):
        vpath = request.root
        for part in parts[1:]:
            ppath = join(vpath, part)
            if exists(ppath):
                vpath = ppath
            else:
                for entry in os.listdir(vpath):
                    if entry.startswith('%'):
                        vpath = join(vpath, entry)
                        request.path.raw[entry[1:]] = part
        request.fs = vpath

def trailing_slash(request):
    if isdir(request.fs):
        if not request.path.raw.endswith('/'):
            parts = list(request.urlparts)
            parts[2] += '/'
            location = urlparse.urlunparse(parts)
            raise Response(301, headers={'Location': location})

def index(request):
    if isdir(request.fs):
        index = join(request.fs, 'index.html')
        if isfile(index):
            request.fs = index

def autoindex(request, want_autoindex, autoindex):
    if isdir(request.fs):
        if want_autoindex:
            request.headers.set('X-Aspen-AutoIndexDir', request.fs)
            request.fs = autoindex 
            assert request.fs is not None # sanity check
        else:
            raise Response(404)

def socket_files(request):
    if 0 and '.sock/' in request.fs:
        parts = request.fs.split('.sock/')
        assert len(parts) == 2
        request.fs = parts[0] + '.sock'
        sockinfo = parts[1].split('/')
        ninfo = len(sockinfo)
        if ninfo >= 1:
            request.transport = sockinfo[0]
        if ninfo >= 2:
            request.session_id = sockinfo[1]
        if ninfo >= 3:
            pass # what is this?

def not_found(request, favicon):
    if not isfile(request.fs):
        if request.path.raw == '/favicon.ico': # special case
            request.fs = favicon
        else:
            raise Response(404)



