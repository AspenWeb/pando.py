from aspen.configuration import Configurable
from aspen.renderers.tornado import Factory as TornadoFactory
from aspen.testing import assert_raises, attach_teardown, fix, FSFIX, mk
from aspen._tornado.template import ParseError


def test_that_a_renderer_factory_is_instantiable():
    actual = TornadoFactory(Configurable.from_argv([])).__class__
    assert actual is TornadoFactory, actual
    


def tornado_factory_factory(argv=None):
    if argv is None:
        argv = []
    return TornadoFactory(Configurable.from_argv(argv))


def test_renderer_renders():
    make_renderer = tornado_factory_factory()
    render = make_renderer("dummy/filepath.txt", "Some bytes!")
    actual = render({})
    assert actual == "Some bytes!", actual

def test_tornado_base_failure_fails():
    mk(("base.html", "{% block foo %}{% end %} Blam."))
    make_renderer = tornado_factory_factory()
    assert_raises( ParseError
                 , make_renderer
                 , "dummy/filepath.txt"
                 , "{% extends base.html %}"
                   "{% block foo %}Some bytes!{% end %}"
                  )

def test_tornado_can_load_bases():
    mk(("base.html", "{% block foo %}{% end %} Blam."))
    make_renderer = tornado_factory_factory(["--project_root", FSFIX])
    render = make_renderer( "<string>"
                          , "{% extends base.html %}"
                            "{% block foo %}Some bytes!{% end %}"
                           )
    actual = render({})
    assert actual == "Some bytes! Blam.", actual

def test_tornado_caches_by_default_after_make_renderer():
    mk(("base.html", "{% block foo %}{% end %} Blam."))
    make_renderer = tornado_factory_factory(["--project_root", FSFIX])
    open(fix("base.html"), "w+").write("{% block foo %}{% end %} Blar.")
    render = make_renderer( "<string>"
                          , "{% extends base.html %}"
                            "{% block foo %}Some bytes!{% end %}"
                           )
    actual = render({})
    assert actual == "Some bytes! Blar.", actual

def test_tornado_caches_by_default():
    mk(("base.html", "{% block foo %}{% end %} Blam."))
    make_renderer = tornado_factory_factory(["--project_root", FSFIX])
    render = make_renderer( "<string>"
                          , "{% extends base.html %}"
                            "{% block foo %}Some bytes!{% end %}"
                           )
    open(fix("base.html"), "w+").write("{% block foo %}{% end %} Blar.")
    actual = render({})
    assert actual == "Some bytes! Blam.", actual

def test_tornado_obeys_changes_reload():
    mk(("base.html", "{% block foo %}{% end %} Blam."))
    make_renderer = tornado_factory_factory([ "--project_root", FSFIX
                                            , "--changes_reload=yes"
                                             ])
    render = make_renderer( "<string>"
                          , "{% extends base.html %}"
                            "{% block foo %}Some bytes!{% end %}"
                           )
    open(fix("base.html"), "w+").write("{% block foo %}{% end %} Blar.")
    actual = render({})
    assert actual == "Some bytes! Blar.", actual

def test_tornado_obeys_changes_reload_for_meta():
    mk(("base.html", "{% block foo %}{% end %} Blam."))
    make_renderer = tornado_factory_factory([ "--project_root", FSFIX
                                            , "--changes_reload=yes"
                                             ])
    open(fix("base.html"), "w+").write("{% block foo %}{% end %} Blar.")
    render = make_renderer( "<string>"
                          , "{% extends base.html %}"
                            "{% block foo %}Some bytes!{% end %}"
                           )
    actual = render({})
    assert actual == "Some bytes! Blar.", actual

def test_cheese_example():
    mk(('configure-aspen.py', """\
from aspen.renderers import Renderer, Factory

class Cheese(Renderer):
    def render_content(self, context):
        return self.compiled.replace("cheese", "CHEESE!!!!!!")

class CheeseFactory(Factory):
    Renderer = Cheese

website.renderer_factories['excited-about-cheese'] = CheeseFactory(website)
"""))
    website = Configurable.from_argv(["--project_root", FSFIX])
    make_renderer = website.renderer_factories['excited-about-cheese']
    render = make_renderer("", "I like cheese!")  # test specline elsewhere
    actual = render({})
    assert actual == "I like CHEESE!!!!!!!", actual


attach_teardown(globals())
