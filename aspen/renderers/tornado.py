

from aspen._tornado.template import Loader, Template

def renderer( rootdir, name, content ):
    """ given a template, return a func that will, when handed a context, return the template rendered with that context """
    loader = Loader( rootdir )
    template = Template( content, name, loader, compress_whitespace = False )
    def _(**context):
        return template.generate(**context)
    return _
