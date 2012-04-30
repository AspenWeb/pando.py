"""Implement pluggable content rendering.

Negotiated and template resources have content pages the bytes for which are
transformed based on context. The user may explicitly choose a renderer per
content page. The default renderer for a page is computed from its media type.
Template resources derive their media type from the file extension. Negotiated
resources have no file extension by definition, so they specify the media type
of their content pages in the resource itself, on the so-called "specline" of
each content page.

A Renderer is instantiated by a Factory, which is a class that is itself
instantied with one argument:

    configuration   an Aspen configuration object


Instances of each Renderer subclass are callables that take three arguments and
return a function (confused yet?). The three arguments are:

    factory         the Factory creating this object
    filepath        the filesystem path of the resource in question
    raw             the bytestring of the page of the resource in question


Each Renderer instance is a callable that takes a context dictionary and
returns a bytestring of rendered content. The heavy lifting is done in the
render_content method. Subclass methods may raise ImportError.

Here's how to implement and register your own renderer:

    from aspen.rendering import Renderer, Factory

    class Cheese(Renderer):
        def render_content(self, compiled, context):
            return compiled.replace("cheese", "CHEESE!!!!!!")

    class CheeseFactory(Factory):
        Renderer = Cheese

    website.renderer_factories['excited-about-cheese'] = CheeseFactory(website)


Now you can use it in a negotiated or template resource:

    ^L #!excited-about-cheese
    I like cheese!


Out will come:

    I like CHEESE!!!!!!!

"""


# abstract bases
# ==============

class Factory(object):

    Renderer = None

    def __init__(self, configuration):
        self._configuration = configuration
        self._changes_reload = configuration.changes_reload
        self.meta = self.compile_meta(configuration)

    def __call__(self, filepath, raw):
        """Given two bytestrings, return a callable.
        """
        self._update_meta()
        return self.Renderer(self, filepath, raw)

    def _update_meta(self):
        if self._changes_reload:
            self.meta = self.compile_meta(self._configuration)
        return self.meta  # used in our child, Renderer

    def compile_meta(self, configuration):
        """Takes a configuration object. Override as needed.

        Whatever you return from this will be set on self.meta the first time
        the factory is called, or every time if changes_reload is True. You can
        then use self.meta in your Renderer class as needed.

        """
        return None


class Renderer(object):

    def __init__(self, factory, filepath, raw):
        """Takes a Factory and two bytestrings.
        """
        self._filepath = filepath
        self._raw = raw
        self._factory = factory
        self._changes_reload = factory._changes_reload
        self.meta = self._factory.meta
        self.compiled = self.compile(self._filepath, self._raw)

    def __call__(self, context):
        if self._changes_reload:
            self.meta = self._factory._update_meta()
            self.compiled = self.compile(self._filepath, self._raw)
        return self.render_content(self.compiled, context)

    def compile(self, filepath, raw):
        """Override.

        Whatever you return from this will be set on self.compiled the first
        time the renderer is called. If changes_reload is True then this will
        be called every time the renderer is called. You can then use
        self.compiled in your render_content method as needed.

        """
        return raw

    def render_content(self, compiled, context):
        """Override. Compiled is whatever compile returns, context is a dict.
        """
        raise NotImplementedError


# tornado
# =======

class TornadoRenderer(Renderer):

    def compile(self, filepath, raw):
        from aspen._tornado.template import Template
        loader = self.meta
        return Template(raw, filepath, loader, compress_whitespace=False)

    def render_content(self, compiled, context):
        return compiled.generate(**context)


class TornadoFactory(Factory):

    Renderer = TornadoRenderer

    def compile_meta(self, configuration):
        from aspen._tornado.template import Loader
        bases_dir = configuration.project_root
        if bases_dir is None:
            loader = None
        else:
            loader = Loader(bases_dir)
        return loader


# pystache
# ========

class PystacheRenderer(Renderer):
    def render_content(self, compiled, context):
        import pystache
        return pystache.render(compiled, context)

class PystacheFactory(Factory):
    Renderer = PystacheRenderer
