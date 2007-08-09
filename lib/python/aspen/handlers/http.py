"""Define some handlers that always return a single HTTP Response.
"""

def HTTP400(environ, start_response):
    start_response('400 Bad Request', [])
    return ['Bad request.']

def HTTP403(environ, start_response):
    start_response('403 Forbidden', [])
    return ['This directory has no index.']

def HTTP404(environ, start_response):
    start_response('404 Not Found', [])
    return ['Resource not found.']

def HTTP500(environ, start_response):
    start_response('500 Internal Server Error', [])
    return ['Internal server error.']

