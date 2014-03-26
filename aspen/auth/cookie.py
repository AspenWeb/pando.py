"""
aspen.auth.cookie
~~~~~~~~~~~~~~~~~

This is a cookie authentication implementation for Aspen.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from aspen import auth
from aspen.utils import to_rfc822, utcnow
from aspen.website import THE_PAST


MINUTE = datetime.timedelta(seconds=60)
HOUR = 60 * MINUTE
DAY  = 24 * HOUR
WEEK = 7 * DAY


TIMEOUT = 2 * HOUR


# Public config knobs
# ===================
# Feel free to set these in, e.g., configure-aspen.py

NAME = "auth"
DOMAIN = None
PATH = "/"
HTTPONLY = "Yes, please."


# Hooks
# =====

def inbound_early(request):
    """Authenticate from a cookie.
    """
    if 'user' not in request.context:
        token = None
        if NAME in request.headers.cookie:
            token = request.headers.cookie[NAME].value
            token = token.decode('US-ASCII')
        request.context['user'] = auth.User(token)


def outbound(response):
    """Set outbound auth cookie.
    """
    if 'user' not in response.request.context:
        # XXX When does this happen? When auth.inbound_early hasn't run, eh?
        raise  # XXX raise what?

    user = response.request.context['user']
    if not isinstance(user, auth.User):
        raise Exception("If you define 'user' in a simplate it has to be an "
                        "instance of an aspen.auth.User.")

    if NAME not in response.request.headers.cookie:
        # no cookie in the request, don't set one on response
        return
    elif user.ANON:
        # user is anonymous, instruct browser to delete any auth cookie
        cookie_value = ''
        cookie_expires = THE_PAST
    else:
        # user is authenticated, keep it rolling for them
        cookie_value = user.token
        cookie_expires = to_rfc822(utcnow() + TIMEOUT)


    # Configure outgoing cookie.
    # ==========================

    response.headers.cookie[NAME] = cookie_value  # creates a cookie object?
    cookie = response.headers.cookie[NAME]          # loads a cookie object?

    cookie['expires'] = cookie_expires

    if DOMAIN is not None:
        # Browser default is the domain of the resource requested.
        # Aspen default is the browser default.
        cookie['domain'] = DOMAIN

    if PATH is not None:
        # XXX What's the browser default? Probably /? Or current dir?
        # Aspen default is "/".
        cookie['path'] = PATH

    if HTTPONLY is not None:
        # Browser default is to allow access from JavaScript.
        # Aspen default is to prevent access from JavaScript.
        cookie['httponly'] = HTTPONLY
