"""
aspen.renderers
+++++++++++++++

This module implements pluggable content rendering.
                                                                              #
See user docs here:

    http://aspen.io/simplates/rendered/

Negotiated and rendered resources have content pages the bytes for which are
transformed based on context. The user may explicitly choose a renderer per
content page, with the default renderer per page computed from its media type.
Template resources derive their media type from the file extension. Negotiated
resources have no file extension by definition, so they specify the media type
of their content pages in the resource itself, on the so-called "specline" of
each content page, like so:

    ^L
    ^L text/plain
    Greetings, program!
    ^L text/html
    <h1>Greetings, program!</h1>


A Renderer is instantiated by a Factory, which is a class that is itself
instantied with one argument:

    configuration   an Aspen configuration object


Instances of each Renderer subclass are callables that take five arguments and
return a function (confused yet?). The five arguments are:

    factory         the Factory creating this object
    filepath        the filesystem path of the resource in question
    raw             the bytestring of the page of the resource in question
    media_type      the media type of the page
    offset          the line number at which the page starts


Each Renderer instance is a callable that takes a context dictionary and
returns a bytestring of rendered content. The heavy lifting is done in the
render_content method.

Here's how to implement and register your own renderer:

    from aspen.renderers import Renderer, Factory

    class Cheese(Renderer):
        def render_content(self, context):
            return self.raw.replace("cheese", "CHEESE!!!!!!")

    class CheeseFactory(Factory):
        Renderer = Cheese

    website.renderer_factories['excited-about-cheese'] = CheeseFactory(website)


You could put that in configure-aspen.py in your --project_root, for example.
Now you can use it in a negotiated or rendered resource:

    ^L #!excited-about-cheese
    I like cheese!


Out will come:

    I like CHEESE!!!!!!!


If you write a new renderer for inclusion in the base Aspen distribution,
please work with Aspen's existing reloading machinery, etc. as much as
possible. Use the existing template shims as guidelines, and if Aspen's
machinery is inadequate for some reason let's evolve the machinery so all
renderers behave consistently for users. Thanks.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


# abstract bases
# ==============
# The base is actually functional. It's a pass-through.

class Renderer(object):

    def __init__(self, factory, filepath, raw, media_type, offset):
        """Takes a Factory, three bytestrings, and an int.
        """
        self._filepath = filepath
        self._factory = factory
        self._changes_reload = factory._changes_reload
        self.meta = self._factory.meta
        self.raw = raw
        self.media_type = media_type
        self.offset = offset
        self.compiled = self.compile(self._filepath, self.raw)

    def __call__(self, context):
        if self._changes_reload:
            self.meta = self._factory._update_meta()
            self.compiled = self.compile(self._filepath, self.raw)
        return self.render_content(context)

    def compile(self, filepath, raw):
        """Override.

        Whatever you return from this will be set on self.compiled the first
        time the renderer is called. If changes_reload is True then this will
        be called every time the renderer is called. You can then use
        self.compiled in your render_content method as needed.

        """
        return raw

    def render_content(self, context):
        """Override. Context is a dict.

        You can use these attributes:

            self.raw        the raw bytes of the content page
            self.compiled   the result of self.compile (generally a template in
                             compiled object form)
            self.meta       the result of Factory.compile_meta
            self.media_type the media type of the page
            self.offset     the line number at which the page starts

        """
        return self.raw  # pass-through


class Factory(object):

    Renderer = Renderer

    def __init__(self, configuration):
        self._configuration = configuration
        self._changes_reload = configuration.changes_reload
        self.meta = self.compile_meta(configuration)

    def __call__(self, filepath, raw, media_type, offset):
        """Given three bytestrings and an int, return a callable.
        """
        self._update_meta()
        return self.Renderer(self, filepath, raw, media_type, offset)

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
