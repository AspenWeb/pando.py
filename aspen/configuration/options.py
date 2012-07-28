import optparse

import aspen


# OptionParser
# ------------

usage = "aspen [options]"


version = """\
aspen, version %s

(c) 2006-2012 Chad Whitacre and contributors
http://aspen.io/
""" % aspen.__version__


description = """\
Aspen is a Python web framework. By default this program will start serving a
website from the current directory on port 8080. Options are as follows. See
also http://aspen.io/.
"""


class DEFAULT(object):
    def __repr__(self):
        return "<DEFAULT>"
DEFAULT = DEFAULT()


def OptionParser():
    optparser = optparse.OptionParser( usage=usage
                                     , version=version
                                     , description=description
                                      )

    basic = optparse.OptionGroup(optparser, "Basic Options")

    basic.add_option( "-f", "--configuration_scripts"
                    , help=("comma-separated list of paths to configuration "
                            "files in Python syntax to exec in addition to "
                            "$ASPEN_PROJECT_ROOT/configure-aspen.py")
                    , default=DEFAULT
                     )
    basic.add_option( "-a", "--network_address"
                    , help=("the IPv4, IPv6, or Unix address to bind to "
                            "[0.0.0.0:8080]")
                    , default=DEFAULT
                     )
    basic.add_option( "-e", "--network_engine"
                    , help=( "the HTTP engine to use, one of "
                           + "{%s}" % ','.join(aspen.NETWORK_ENGINES)
                           + " [%s]" % aspen.NETWORK_ENGINES[1]
                            )
                    , default=DEFAULT
                     )
    basic.add_option( "-l", "--logging_threshold"
                    , help=("a small integer; 1 will suppress most of aspen's "
                            "internal logging, 2 will suppress all it [0]")
                    , default=DEFAULT
                     )
    basic.add_option( "-p", "--project_root"
                    , help=("the filesystem path of the directory in "
                            "which to look for project files like "
                            "template bases and such, relative to "
                            "$ASPEN_WWW_ROOT []")
                    , default=DEFAULT
                     )
    basic.add_option( "-w", "--www_root"
                    , help=("the filesystem path of the document "
                            "publishing root [.]")
                    , default=DEFAULT
                     )


    extended = optparse.OptionGroup( optparser, "Extended Options"
                                   , "I judge these variables to be less-"
                                     "often configured from the command "
                                     "line. But who knows?"
                                    )
    extended.add_option( "--changes_reload"
                       , help=("if set to yes/true/1, changes to configuration"
                               " files and Python modules will cause aspen to "
                               "re-exec, and template bases won't be cached "
                               "[no]")

                       , default=DEFAULT
                        )
    extended.add_option( "--charset_dynamic"
                       , help=("this is set as the charset for rendered and "
                               "negotiated resources of Content-Type text/* "
                               "[UTF-8]")
                       , default=DEFAULT
                        )
    extended.add_option( "--charset_static"
                       , help=("if set, this will be sent as the charset for "
                               "static resources of Content-Type text/*; if "
                               "you want to punt and let browsers guess, then "
                               "just leave this unset []")
                       , default=DEFAULT
                        )
    extended.add_option( "--indices"
                       , help=("a comma-separated list of filenames to look "
                               "for when a directory is requested directly; "
                               "prefix with + to extend previous "
                               "configuration instead of overriding "
                               "[index.html, index.json]")
                       , default=DEFAULT
                        )
    extended.add_option( "--unavailable"
                       , help=("a non-negative integer, the number of minutes "
                               "the site is expected to be down for "
                               "maintenance. If set to non-zero, all requests "
                               "will get a 503 response, and the Retry-After "
                               "header will be set [0]")
                       , default=DEFAULT
                        )
    extended.add_option( "--list_directories"
                       , help=("if set to {yes,true,1}, aspen will serve a "
                               "directory listing when no index is available "
                               "[no]")
                       , default=DEFAULT
                        )
    extended.add_option( "--media_type_default"
                       , help=("this is set as the Content-Type for resources "
                               "of otherwise unknown media type [text/plain]")
                       , default=DEFAULT
                        )
    extended.add_option( "--media_type_json"
                       , help=("this is set as the Content-Type of JSON "
                               "resources [application/json]")
                       , default=DEFAULT
                        )
    extended.add_option( "--renderer_default"
                    , help=( "the renderer to use by default; one of "
                           + "{%s}" % ','.join(aspen.RENDERERS)
                           + " [tornado]"
                            )
                    , default=DEFAULT
                     )
    extended.add_option( "--show_tracebacks"
                       , help=("if set to {yes,true,1}, 500s will have a "
                               "traceback in the browser [no]")
                       , default=DEFAULT
                        )


    optparser.add_option_group(basic)
    optparser.add_option_group(extended)
    return optparser
