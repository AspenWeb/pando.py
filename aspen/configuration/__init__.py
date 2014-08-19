"""
aspen.configuration
+++++++++++++++++++

Define configuration objects.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import errno
import mimetypes
import os
import sys
import traceback
import pkg_resources
from collections import defaultdict

import aspen
import aspen.logging
from aspen.configuration import parse
from aspen.configuration.exceptions import ConfigurationError
from aspen.configuration.options import OptionParser, DEFAULT
from aspen.utils import ascii_dammit
from aspen.typecasting import defaults as default_typecasters
import aspen.body_parsers


# Defaults
# ========
# The from_unicode callable converts from unicode to whatever format is
# required by the variable, raising ValueError appropriately. Note that
# name is supposed to match the options in our optparser. I like it wet.

KNOBS = \
    { 'configuration_scripts': (lambda: [], parse.list_)
    , 'project_root':       (None, parse.identity)
    , 'logging_threshold':  (0, int)
    , 'www_root':           (None, parse.identity)


    # Extended Options
    # 'name':               (default, from_unicode)
    , 'changes_reload':     (False, parse.yes_no)
    , 'charset_dynamic':    ('UTF-8', parse.charset)
    , 'charset_static':     (None, parse.charset)
    , 'indices':            ( lambda: ['index.html', 'index.json', 'index'] +
                                      ['index.html.spt', 'index.json.spt', 'index.spt']
                            , parse.list_
                             )
    , 'list_directories':   (False, parse.yes_no)
    , 'media_type_default': ('text/plain', parse.media_type)
    , 'media_type_json':    ('application/json', parse.media_type)
    , 'renderer_default':   ('stdlib_percent', parse.renderer)
    , 'show_tracebacks':    (False, parse.yes_no)
     }

DEFAULT_CONFIG_FILE = 'configure-aspen.py'

# Configurable
# ============
# Designed as a singleton.

class Configurable(object):
    """Mixin object for aggregating configuration from several sources.
    """

    protected = False  # Set to True to require authentication for all
                       # requests.

    @classmethod
    def from_argv(cls, argv):
        """return a Configurable based on the passed-in arguments list
        """
        configurable = cls()
        configurable.configure(argv)
        return configurable


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
        error = None
        try:
            value = raw
            if isinstance(value, str):
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

        self.typecasters = default_typecasters

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


        def safe_getcwd(errorstr):
            try:
                # If the working directory no longer exists, then the following
                # will raise OSError: [Errno 2] No such file or directory. I
                # swear I've seen this under supervisor, though I don't have
                # steps to reproduce. :-(  To get around this you specify a
                # www_root explicitly, or you can use supervisor's cwd
                # facility.

                return os.getcwd()
            except OSError, err:
                if err.errno != errno.ENOENT:
                    raise
                raise ConfigurationError(errorstr)



        # LOGGING_THRESHOLD
        # -----------------
        # This is initially set to -1 and not 0 so that we can tell if the user
        # changed it programmatically directly before we got here. I do this in
        # the testing module, that's really what this is about.
        if aspen.logging.LOGGING_THRESHOLD == -1:
            aspen.logging.LOGGING_THRESHOLD = self.logging_threshold
        # Now that we know the user's desires, we can log appropriately.
        aspen.log_dammit(os.linesep.join(msgs))

        # project root
        if self.project_root is None:
            aspen.log_dammit("project_root not configured (no template bases, "
                             "etc.).")
        else:
            # canonicalize it
            if not os.path.isabs(self.project_root):
                aspen.log_dammit("project_root is relative to CWD: '%s'."
                                 % self.project_root)
                cwd = safe_getcwd("Could not get a current working "
                                  "directory. You can specify "
                                  "ASPEN_PROJECT_ROOT in the environment, "
                                  "or --project_root on the command line.")
                self.project_root = os.path.join(cwd, self.project_root)

            self.project_root = os.path.realpath(self.project_root)
            aspen.log_dammit("project_root set to %s." % self.project_root)

            # mime.types
            users_mimetypes = os.path.join(self.project_root, 'mime.types')
            mimetypes.knownfiles += [users_mimetypes]

            # configure-aspen.py
            configure_aspen_py = os.path.join( self.project_root
                                             , DEFAULT_CONFIG_FILE
                                              )
            self.configuration_scripts.append(configure_aspen_py)  # last word

            # PYTHONPATH
            sys.path.insert(0, self.project_root)

        # www_root
        if self.www_root is None:
            self.www_root = safe_getcwd("Could not get a current working "
                                         "directory. You can specify "
                                         "ASPEN_WWW_ROOT in the environment, "
                                         "or --www_root on the command line.")

        self.www_root = os.path.realpath(self.www_root)

        # load bodyparsers
        self.body_parsers = {
            "application/x-www-form-urlencoded": aspen.body_parsers.formdata,
            "multipart/form-data": aspen.body_parsers.formdata,
            self.media_type_json: aspen.body_parsers.jsondata
            }

        # load renderers
        self.renderer_factories = {}
        for name in aspen.BUILTIN_RENDERERS:
            # Pre-populate renderers so we can report on ImportErrors early
            try:
                capture = {}
                python_syntax = 'from aspen.renderers.%s import Factory'
                exec python_syntax % name in capture
                make_renderer = capture['Factory'](self)
            except ImportError, err:
                make_renderer = err
                err.info = sys.exc_info()
            self.renderer_factories[name] = make_renderer

        for entrypoint in pkg_resources.iter_entry_points(group='aspen.renderers'):
            render_module = entrypoint.load()
            self.renderer_factories[entrypoint.name] = render_module.Factory(self)
            aspen.log_dammit("Found plugin for renderer '%s'" % entrypoint.name)

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

        self.run_config_scripts()
        self.show_renderers()

    def show_renderers(self):
        aspen.log_dammit("Renderers (*ed are unavailable, CAPS is default):")
        width = max(map(len, self.renderer_factories))
        for name, factory in self.renderer_factories.items():
            star = " "
            if isinstance(factory, ImportError):
                star = "*"
                error = "ImportError: " + factory.args[0]
            else:
                error = ""
            if name == self.renderer_default:
                name = name.upper()
            name = name.ljust(width + 2)
            aspen.log_dammit(" %s%s%s" % (star, name, error))

        default_renderer = self.renderer_factories[self.renderer_default]
        if isinstance(default_renderer, ImportError):
            msg = "\033[1;31mImportError loading the default renderer, %s:\033[0m"
            aspen.log_dammit(msg % self.renderer_default)
            sys.excepthook(*default_renderer.info)
            raise default_renderer


    def run_config_scripts(self):
        # Finally, exec any configuration scripts.
        # ========================================
        # The user gets self as 'website' inside their configuration scripts.
        default_cfg_filename = None
        if self.project_root is not None:
            default_cfg_filename = os.path.join(self.project_root, DEFAULT_CONFIG_FILE)

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
                # Re-raise the error if it happened inside the script.
                if err.filename != filepath:
                    raise

                # I was checking os.path.isfile for these, but then we have a
                # race condition that smells to me like a potential security
                # vulnerability.

                ## determine if it's a default configscript or a specified one
                cfgtype = "configuration"
                if filepath == default_cfg_filename:
                    cfgtype = "default " + cfgtype
                ## pick the right error mesage
                if err.errno == errno.ENOENT:
                    msg = ("The %s script %s doesn't seem to exist.")
                elif err.errno == errno.EACCES:
                    msg = ("It appears that you don't have permission to read "
                           "the %s script %s.")
                else:
                    msg = ("There was a problem reading the %s script %s:")
                    msg += os.sep + traceback.format_exc()
                ## do message-string substitutions
                msg = msg % (cfgtype, filepath)
                ## output the message
                if not "default" in cfgtype:
                   # if you specify a config file, it's an error if there's a problem
                   raise ConfigurationError(msg)
                else:
                   # problems with default config files are okay, but get logged
                   aspen.log(msg)




