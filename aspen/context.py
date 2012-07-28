class Context(dict):
    """Model the execution context for a Resource.
    """

    def __init__(self, request):
        """Takes a Request object.
        """
        self.website    = None # set in dynamic_resource.py
        self.body       = request.body
        self.headers    = request.headers
        self.cookie     = request.headers.cookie
        self.path       = request.line.uri.path
        self.qs         = request.line.uri.querystring
        self.request    = request
        self.socket     = None
        self.channel    = None
        self.context    = self

        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html
        for method in ['OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE',
                       'TRACE', 'CONNECT']:
            self[method] = (method == request.line.method)
            setattr(self, method, self[method])

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError("")

    def __setattr__(self, name, value):
        self[name] = value
