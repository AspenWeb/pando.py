

def renderer( rootdir, name, content ):
    """ given a template, return a func that will, when handed a context, return the template rendered with that context """
    import pystache
    def _(context):
        return pystache.render( content, context)
    return _

