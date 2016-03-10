"""
aspen.request_processor
+++++++++++++++++++++++
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import errno
import mimetypes
import os
import sys
from collections import defaultdict

from algorithm import Algorithm

from . import parse
from .typecasting import defaults as default_typecasters
from ..utils import ascii_dammit
from ..simplates.renderers import factories


class ConfigurationError(StandardError):
    """This is an error in any part of our configuration.
    """

    def __init__(self, msg):
        StandardError.__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg


default_indices = lambda: ['index.html', 'index.json', 'index',
                           'index.html.spt', 'index.json.spt', 'index.spt']


    # 'name':               (default,               from_unicode)
KNOBS = \
    { 'base_url':           ('',                    parse.identity)
    , 'changes_reload':     (False,                 parse.yes_no)
    , 'charset_dynamic':    ('UTF-8',               parse.charset)
    , 'charset_static':     (None,                  parse.charset)
    , 'indices':            (default_indices,       parse.list_)
    , 'media_type_default': ('text/plain',          parse.media_type)
    , 'media_type_json':    ('application/json',    parse.media_type)
    , 'project_root':       (None,                  parse.identity)
    , 'renderer_default':   ('stdlib_percent',      parse.renderer)
    , 'www_root':           (None,                  parse.identity)
     }


class RequestProcessor(object):
    """Define a parasitic request processor.

    It depends on a host framework for real request/response objects.

    """

    def __init__(self, **kwargs):
        """Takes configuration in kwargs.
        """
        self.algorithm = Algorithm.from_dotted_name('aspen.request_processor.algorithm')
        self.configure(**kwargs)


    def process(self, path, querystring, accept_header, raise_immediately=None, return_after=None):
        """Given a path, querystring, and Accept header, return a state dict.
        """
        return self.algorithm.run( request_processor=self
                                 , path=path
                                 , querystring=querystring
                                 , accept_header=accept_header
                                 , _raise_immediately=raise_immediately
                                 , _return_after=return_after
                                  )


    def _set(self, name, hydrated, flat, context, name_in_context):
        """Set value at self.name, calling hydrated if it's callable.
        """
        if callable(hydrated):
            hydrated = hydrated()  # Call it if we can.
        setattr(self, name, hydrated)
        if name_in_context:
            assert isinstance(flat, unicode) # sanity check
            name_in_context = " %s=%s" % (name_in_context, flat)
        out = "  %-22s %-30s %-24s"
        return out % (name, hydrated, context + name_in_context)

    def set(self, name, raw, from_unicode, context, name_in_context):
        error = None
        try:
            value = raw
            if isinstance(value, str):
                value = raw.decode('US-ASCII')
            hydrated = from_unicode(value)
        except UnicodeDecodeError as error:
            value = ascii_dammit(value)
            error_detail = "Configuration values must be US-ASCII."
        except ValueError as error:
            error_detail = error.args[0]

        if error is not None:
            msg = "Got a bad value '%s' for %s %s:"
            msg %= (value, context, name_in_context)
            if error_detail:
                msg += " " + error_detail + "."
            raise ConfigurationError(msg)

        # special-case lists, so we can layer them
        if from_unicode is parse.list_:
            extend, new_value = hydrated
            if extend:
                old_value = getattr(self, name)
                hydrated = old_value + new_value
            else:
                hydrated = new_value

        args = (name, hydrated, value, context, name_in_context)
        return self._set(*args)

    def configure(self, **kwargs):
        """Takes a dictionary of strings/unicodes to strings/unicodes.
        """

        # Do some base-line configuration.
        # ================================
        # We want to do the following configuration of our Python environment
        # regardless of the user's configuration preferences

        # mimetypes
        aspens_mimetypes = os.path.join(os.path.dirname(__file__), 'mime.types')
        mimetypes.knownfiles += [aspens_mimetypes]
        # mimetypes.init is called below after the user has a turn.

        # XXX register codecs here

        self.typecasters = default_typecasters


        # Configure from defaults, environment, and kwargs.
        # =================================================

        for name, (default, func) in sorted(KNOBS.items()):

            # set the default value for this variable
            self._set(name, default, None, "default", '')

            # set from the environment
            envvar = 'ASPEN_' + name.upper()
            value = os.environ.get(envvar, '').strip()

            # set from kwargs
            value = kwargs.get(name)
            if value is not None:
                self.set(name, value, func, "kwargs", name)


        # Set some attributes.
        # ====================

        def safe_getcwd(errorstr):
            try:
                # If the working directory no longer exists, then the following
                # will raise OSError: [Errno 2] No such file or directory. I
                # swear I've seen this under supervisor, though I don't have
                # steps to reproduce. :-(  To get around this you specify a
                # www_root explicitly, or you can use supervisor's cwd
                # facility.

                return os.getcwd()
            except OSError as err:
                if err.errno != errno.ENOENT:
                    raise
                raise ConfigurationError(errorstr)

        # project root
        if self.project_root is not None:
            # canonicalize it
            if not os.path.isabs(self.project_root):
                cwd = safe_getcwd("Could not get a current working "
                                  "directory. You can specify "
                                  "ASPEN_PROJECT_ROOT in the environment, "
                                  "or project_root in kwargs.")
                self.project_root = os.path.join(cwd, self.project_root)

            self.project_root = os.path.realpath(self.project_root)

            # mime.types
            users_mimetypes = os.path.join(self.project_root, 'mime.types')
            mimetypes.knownfiles += [users_mimetypes]

            # PYTHONPATH
            sys.path.insert(0, self.project_root)

        # www_root
        if self.www_root is None:
            self.www_root = safe_getcwd("Could not get a current working "
                                         "directory. You can specify "
                                         "ASPEN_WWW_ROOT in the environment, "
                                         "or www_root in kwargs.")

        self.www_root = os.path.realpath(self.www_root)

        # load renderers
        self.renderer_factories = factories(self)

        self.default_renderers_by_media_type = defaultdict(lambda: self.renderer_default)
        self.default_renderers_by_media_type[self.media_type_json] = 'json_dump'

        # mime.types
        # ==========
        # It turns out that init'ing mimetypes is somewhat expensive. This is
        # significant in testing, though in dev/production you wouldn't notice.
        # In any case this means that if a devuser inits mimetypes themselves
        # then we won't do so again here, which is fine. Right?

        if not mimetypes.inited:
            mimetypes.init()
