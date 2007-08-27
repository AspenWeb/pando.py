import mimetypes
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

        # 1. Check for file
        # =================

        fspath = environ['PATH_TRANSLATED']
        assert isfile(fspath), "This handler only serves files."


        # 2. Load simplate
        # ================

        namespace, script, template  = self.load_simplate(fspath)


        # 3. Populate namespace
        # =====================
        # We need to keep track of whether the script calls start_response.

        namespace['environ'] = environ

        _START_RESPONSE_CALLED = False
        def _start_response(response, headers):
            _START_RESPONSE_CALLED = True
            return start_response(response, headers)

        namespace['start_response'] = _start_response


        # 4. Run the script
        # =================

        WANT_TEMPLATE = True
        if script:
            try:
                exec script in namespace
            except SystemExit:
                pass


        # 5. Get a response
        # =================

        if 'response' in namespace:
            response = namespace['response']
            WANT_TEMPLATE = False
        else:
            response = []


        # 6. Render the template
        # ======================

        if WANT_TEMPLATE:
            response = [template % namespace]
        if not _START_RESPONSE_CALLED:
            guess = mimetypes.guess_type(fspath, 'text/plain')[0]
            start_response('200 OK', [('Content-Type', guess)])


        # 7. Return
        # =========

        return response


wsgi = WSGISimplate()