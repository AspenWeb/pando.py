from os.path import isfile

from aspen.handlers.simplates.base import BaseSimplate


class WSGISimplate(BaseSimplate):
    """Basic simplate implementation depending only on the standard library.
    """

    def compile_template(self, template):
        """Implement BaseSimplate requirement as a pass-through.
        """
        return template

    def __call__(self, environ, start_response):
        """WSGI contract.
        """
        fspath = environ['PATH_TRANSLATED']
        assert isfile(fspath), "This handler only serves files."

        namespace, script, template  = self.load_simplate(fspath)

        namespace['__file__'] = fspath
        namespace['environ'] = environ
        namespace['start_response'] = start_response

        if script:
            try:
                exec script in namespace
            except SystemExit:
                pass

        start_response('200 OK', [()])

        if 'response' in namespace:
            response = namespace['response']
        else:
            response = [template % namespace]

        return response


wsgi = WSGISimplate()