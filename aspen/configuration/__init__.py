"""Define configuration objects.
"""
import errno
import mimetypes
import os
import socket
import sys

import aspen
from aspen.utils import ascii_dammit
from aspen.configuration import parse
from aspen.configuration.exceptions import ConfigurationError
from aspen.configuration.hooks import Hooks
from aspen.configuration.options import OptionParser, DEFAULT
from aspen.renderers.tornado import renderer as tornado_renderer



# Non-caching Renderer
# ====================
# This is used when follow_filesystem is True.

def RecompilingRenderer(renderer):
    def _(*a):
        return renderer(*a)
    return _


# Defaults
# ========
# The from_unicode callable converts from unicode to whatever format is 
# required by the variable, raising ValueError appropriately. Note that 
# name is supposed to match the options in our optparser. I like it wet.

KNOBS = \
    { 'configuration_scripts': (lambda: [], parse.list_)
    , 'network_engine':     (u'cherrypy', parse.network_engine)
    , 'network_address':    ( ((u'0.0.0.0', 8080), socket.AF_INET)
                            , parse.network_address
                             )
    , 'project_root':       (None, parse.identity)
    , 'logging_threshold':  (0, int)
    , 'www_root':           (None, parse.identity)


    # Extended Options
    # 'name':               (default, from_unicode)
    , 'changes_reload':     (False, parse.yes_no)
    , 'charset_dynamic':    (u'UTF-8', parse.charset)
    , 'charset_static':     (None, parse.charset)
    , 'indices':            ( lambda: [u'index.html', u'index.json']
                            , parse.list_ 
                             )
    , 'list_directories':   (False, parse.yes_no)
    , 'media_type_default': (u'text/plain', parse.media_type)
    , 'media_type_json':    (u'application/json', parse.media_type)
    , 'show_tracebacks':    (False, parse.yes_no)
     }


# Configurable
# ============
# Designed as a singleton.

class Configurable(object):
    """Mixin object for aggregating configuration from several sources.
    """

    def _set(self, name, hydrated, flat, context, name_in_context):
        """Set value at self.name, calling value if it's callable.
        """
        if aspen.is_callable(hydrated):
            hydrated = hydrated()  # Call it if we can.
        setattr(self, name, hydrated)
        if name_in_context:
            assert isinstance(flat, unicode) # sanity check
            name_in_context = " %s=%s" % (name_in_context, flat)
        out = "  %-22s %-30s %-24s" 
        return out % (name, hydrated, context + name_in_context)

    def set(self, name, raw, from_unicode, context, name_in_context):
        assert isinstance(raw, str), "%s isn't a bytestring" % name

        error = None
        try:
            value = raw.decode('US-ASCII')
            hydrated = from_unicode(value)
        except UnicodeDecodeError, error:
            value = ascii_dammit(value)
            error_detail = "Configuration values must be US-ASCII."
        except ValueError, error:
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

    def configure(self, argv):
        """Takes an argv list, and gives it straight to optparser.parse_args.

        The argv list should not include the executable name.

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


        # Parse argv.
        # ===========

        opts, args = OptionParser().parse_args(argv)


        # Configure from defaults, environment, and command line.
        # =======================================================

        msgs = ["Reading configuration from defaults, environment, and "
                "command line."] # can't actually log until configured

        for name, (default, func) in sorted(KNOBS.items()):

            # set the default value for this variable
            msgs.append(self._set(name, default, None, "default", ''))

            # set from the environment
            envvar = 'ASPEN_' + name.upper()
            value = os.environ.get(envvar, '').strip()
            if value:
                msgs.append(self.set( name
                                    , value
                                    , func
                                    , "environment variable"
                                    , envvar
                                     ))

            # set from the command line
            value = getattr(opts, name)
            if value is not DEFAULT:
                msgs.append(self.set( name
                                    , value
                                    , func
                                    , "command line option"
                                    , "--"+name
                                     ))


        # Set some attributes.
        # ====================

        # LOGGING_THRESHOLD
        aspen.LOGGING_THRESHOLD = self.logging_threshold
        # Now that we know the user's desires, we can log appropriately.
        aspen.log_dammit(os.linesep.join(msgs))
       
        # www_root
        if self.www_root is None:
            try:

                # If the working directory no longer exists, then the following
                # will raise OSError: [Errno 2] No such file or directory. I
                # swear I've seen this under supervisor, though I don't have
                # steps to reproduce. :-(  To get around this you specify a
                # www_root explicitly, or you can use supervisor's cwd
                # facility.

                self.www_root = os.getcwd()
            except OSError, err:
                if err.errno != errno.ENOENT:
                    raise
                raise ConfigurationError("Could not get a current working "
                                         "directory. You can specify "
                                         "ASPEN_WWW_ROOT in the environment, "
                                         "or --www_root on the command line.")

        self.www_root = os.path.realpath(self.www_root)
        os.chdir(self.www_root)

        self.template_loaders = { 'tornado': tornado_renderer }
        self.template_loader_default = 'tornado'

        # project root 
        if self.project_root is None:
            aspen.log_dammit("project_root not configured (no template bases, "
                             "etc.).")
            configure_aspen_py = None
        else:
            # canonicalize it
            if not os.path.isabs(self.project_root):
                aspen.log_dammit("project_root is relative: '%s'." 
                                 % self.project_root)
                self.project_root = os.path.join( self.www_root
                                                , self.project_root
                                                 )
            self.project_root = os.path.realpath(self.project_root)
            aspen.log_dammit("project_root set to %s." % self.project_root)

            # template loader
            if self.changes_reload:
                for k, v in self.template_loaders.items():
                    self.template_loaders[k] = RecompilingRenderer(v)
            
            # mime.types
            users_mimetypes = os.path.join(self.project_root, 'mime.types')
            mimetypes.knownfiles += [users_mimetypes]

            # configure-aspen.py
            configure_aspen_py = os.path.join( self.project_root
                                             , 'configure-aspen.py'
                                              )
            self.configuration_scripts.append(configure_aspen_py)  # last word

            # PYTHONPATH
            sys.path.insert(0, self.project_root)

        # mime.types
        mimetypes.init()

        # network_engine
        try: 
            cap = {}
            python_syntax = 'from aspen.engines.%s_ import Engine' 
            exec python_syntax % self.network_engine in cap
            Engine = cap['Engine']
        except ImportError:
            # ANSI colors: 
            #   http://stackoverflow.com/questions/287871/
            #   http://en.wikipedia.org/wiki/ANSI_escape_code#CSI_codes
            #   XXX consider http://pypi.python.org/pypi/colorama
            msg = "\033[1;31mImportError loading the %s engine:\033[0m%s" 
            aspen.log_dammit(msg % (self.network_engine, os.sep))
            raise
        self.network_engine = Engine(self.network_engine, self)

        # network_address, network_sockfam, network_port
        self.network_address, self.network_sockfam = self.network_address
        if self.network_sockfam == socket.AF_INET:
            self.network_port = self.network_address[1]
        else:
            self.network_port = None

        # hooks
        self.hooks = Hooks([ 'startup'
                           , 'inbound_early'
                           , 'inbound_late'
                           , 'outbound_early'
                           , 'outbound_late'
                           , 'shutdown'
                            ])


        # Finally, exec any configuration scripts.
        # ========================================
        # The user gets self as 'website' inside their configuration scripts.
       
        for filepath in self.configuration_scripts:
            if not filepath.startswith(os.sep):
                if self.project_root is None:
                    raise ConfigurationError("You must set project_root in "
                                             "order to specify a configuratio"
                                             "n_script relatively.")
                filepath = os.path.join(self.project_root, filepath)
                filepath = os.path.realpath(filepath)
            try:
                execfile(filepath, {'website': self})
            except IOError, err:
                # I was checking os.path.isfile for these, but then we have a 
                # race condition that smells to me like a potential security 
                # vulnerability.
                if err.errno == errno.ENOENT:
                    msg = ("The configuration script %s doesn't seem to "
                           "exist.")
                elif err.errno == errno.EACCES:
                    msg = ("It appears that you don't have permission to read "
                           "the configuration script %s.")
                else:
                    import traceback
                    msg = ("There was a problem reading the configuration "
                           "script %s:")
                    msg += os.sep + traceback.format_exc()
                if configure_aspen_py is not None:
                    if filepath == configure_aspen_py:
                        # Special-case this magically-named configuration file.
                        aspen.log("Default configuration script not found: %s."
                                  % filepath)
                    else:
                        raise ConfigurationError(msg % filepath)


    @classmethod
    def from_argv(cls, argv):
        o = cls()
        o.configure(argv)
        return o
