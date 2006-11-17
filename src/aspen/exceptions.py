from os.path import join


class AspenError(StandardError):
    def __init__(self, msg):
        self.msg = msg

class HandlerError(AspenError): pass
class HookError(AspenError): pass
class RuleError(AspenError): pass


class ConfigError(AspenError):
    def __init__(self, msg, filename, lineno):
        AspenError.__init__(self, msg)
        self.filename = filename
        self.lineno = int(lineno)
        self.args = (msg, filename, lineno)
    def __str__(self):
        opts = (self.msg, self.filename, self.lineno)
        return '%s (%s, line %d)' % opts
    __repr__ = __str__

class AppsConfError(ConfigError):
    def __init__(self, msg, lineno):
        filename = join('__', 'etc', 'apps.conf')
        ConfigError.__init__(self, msg, filename, lineno)

class HandlersConfError(ConfigError):
    def __init__(self, msg, lineno):
        filename = join('__', 'etc', 'handlers.conf')
        ConfigError.__init__(self, msg, filename, lineno)

class MiddlewareConfError(ConfigError):
    def __init__(self, msg, lineno):
        filename = join('__', 'etc', 'middleware.conf')
        ConfigError.__init__(self, msg, filename, lineno)
