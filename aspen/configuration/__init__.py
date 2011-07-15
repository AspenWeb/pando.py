"""Define configuration objects.
"""
import logging
import mimetypes
import os
import socket
import sys
from os.path import dirname, expanduser, isdir, join, realpath

import aspen
from aspen.configuration.aspenconf import AspenConf 
from aspen.configuration.exceptions import ConfigurationError
from aspen.configuration.hooks import HooksConf
from aspen.configuration.optparser import optparser, validate_address
from aspen._tornado.template import Loader
from aspen.configuration.logging_ import configure_logging
from aspen.configuration.colon import colonize


class Configurable(object):
    """Mixin object for aggregating configuration from several sources.
    """

    def configure(self, argv):
        """Takes an argv list, and gives it straight to optparser.parse_args.

        The argv list should not include the executable name.

        """

        self.__names = [] # keep track of what configuration we configure


        # Parse argv.
        # ===========

        opts, args = optparser.parse_args(argv)


        # Orient ourselves.
        # =================

        self.root = root = find_root(args)
        os.chdir(root)

        self.dotaspen = dotaspen = join(self.root, '.aspen')
        if isdir(dotaspen):
            if sys.path[0] != dotaspen:
                sys.path.insert(0, dotaspen)

        self.__names.extend(['root', 'dotaspen'])


        # Set some attributes.
        # ====================

        self.conf = load_conf(expanduser, dotaspen)
        self.template_loader = Loader(dotaspen)
        self.__names.extend(['conf', 'template_loader'])

        init_mimetypes(mimetypes, dotaspen)
        self.default_mimetype = load_default_mimetype(self.conf)
        self.default_filenames = load_default_filenames(self.conf)
        self.json_content_type = load_json_content_type(self.conf)
        self.show_tracebacks = self.conf.aspen.no('show_tracebacks')
        self.__names.extend(['default_mimetype', 'default_filenames', 
            'json_content_type', 'show_tracebacks'])

        self.hooks = load_hooks(expanduser, dotaspen)
        self.__names.append('hooks')

        self.engine = load_engine(opts, self)
        self.changes_kill = self.conf['aspen.cli'].no('changes_kill')
        self.__names.extend(['engine', 'changes_kill'])

        self.address, self.sockfam = load_address_sockfam(opts, self.conf)
        self.port = load_port(self.address, self.sockfam)
        self.sock = None
        self.__names.extend(['address', 'sockfam', 'port', 'sock'])

        r = configure_logging(opts, dotaspen, self.conf)
        self.log_filename, self.log_filter, self.log_format, self.log_level = r
        self.__names.extend(['log_filename', 'log_filter', 'log_format', 
            'log_level'])

    
    @classmethod
    def from_argv(cls, argv):
        o = cls()
        o.configure(argv)
        return o

    def copy_configuration_to(self, other):
        """Given another object, shallow copy attributes to it.
        """
        for name in self.__names:
            setattr(other, name, getattr(self, name))

def find_root(args):        
    """This can only be passed on the command line.
    """
    if args:
        root = args[0]
    else:
        try:
            # Under supervisord, the following raises 
            #   OSError: [Errno 2] No such file or directory
            # So be sure to pass a directory in on the command line, or cwd
            # using supervisord's own facility for that.
            root = os.getcwd()
        except OSError:
            raise ConfigurationError("Could not get a current working "
                                     "directory. You can specify the site "
                                     "root on the command line.")
    root = realpath(root)
    if not isdir(root):
        msg = "%s does not point to a directory" % root
        raise ConfigurationError(msg)
    return root

def load_conf(expanduser, dotaspen):
    return AspenConf( '/etc/aspen/aspen.conf'
                    , '/usr/local/etc/aspen/aspen.conf'
                    , expanduser('~/.aspen/aspen.conf') 
                    , join(dotaspen, 'aspen.conf')
                     ) # later overrides earlier

def init_mimetypes(mimetypes, dotaspen):
    mimetypes.knownfiles = [ join(dirname(__file__), 'mime.types')
                           , '/etc/mime.types'
                           , '/usr/local/etc/mime.types'
                           , join(dotaspen, 'mime.types')
                            ] # later overrides earlier
    mimetypes.init()

def load_engine(opts, configuration):
    conf = configuration.conf
    if opts.engine is not None:     # use command line if present
        engine_name = opts.engine
    else:                           # fall back to aspen.conf
        engine_name = conf['aspen.cli'].get('engine', aspen.ENGINES[0])
        if engine_name not in aspen.ENGINES:
            msg = "engine is not one of {%s}: %%s" % (','.join(aspen.ENGINES))
            raise ConfigurationError(msg % engine)
    try: 
        exec 'from aspen.engines.%s_ import Engine' % engine_name
    except ImportError:
        # ANSI colors: 
        #   http://stackoverflow.com/questions/287871/
        #   http://en.wikipedia.org/wiki/ANSI_escape_code#CSI_codes
        print >> sys.stderr
        print >> sys.stderr, ( "\033[1;31mImportError loading the "
                             + "%s engine:\033[0m" % engine_name
                              )
        print >> sys.stderr
        raise

    engine = Engine(engine_name, configuration)
    return engine

def load_default_mimetype(conf):
    return conf.aspen.get('default_mimetype', 'text/plain')

def load_default_filenames(conf):
    default_filenames = conf.aspen.get('default_filenames', 'index.html')
    default_filenames = default_filenames.split()
    default_filenames = [x.strip(',') for x in default_filenames]
    default_filenames = [x for x in default_filenames if x]
    default_filenames = [x.split(',') for x in default_filenames]
    out = []
    for nested in default_filenames:
        out.extend(nested)
    return out

def load_json_content_type(conf):
    return conf.aspen.get('json_content_type', 'application/json')

def load_hooks(expanduser, dotaspen):
    return HooksConf( join(dirname(__file__), 'hooks.conf')
                    , '/etc/aspen/hooks.conf'
                    , '/usr/local/etc/aspen/hooks.conf'
                    , expanduser('~/.aspen/hooks.conf')
                    , join(dotaspen, 'hooks.conf')
                     ) # later comes after earlier, per section

def load_address_sockfam(opts, conf):
    """These can be set either on the command line or in the conf file.
    """
    if getattr(opts, 'have_address', False):        # first check CLI
        address = opts.address
        sockfam = opts.sockfam
    elif 'address' in conf['aspen.cli']:            # then check conf
        address, sockfam = validate_address(conf['aspen.cli']['address'])
    else:                                           # default from optparse
        address = opts.address
        sockfam = socket.AF_INET

    return address, sockfam

def load_port(address, sockfam):
    if sockfam == socket.AF_INET:
        port = address[1]
    else:
        port = None
    return port

