import mimetypes
from os.path import isfile

from django.core.handlers.wsgi import WSGIHandler


class WSGI(WSGIHandler):
    """This WSGI app serves PATH_TRANSLATED as a Django script or template.
    """

    filetype = '' # 'script' or 'template' or 'scrimplate'

    def get_response(self, request):
        """Extend WSGIHandler.get_response to bypass usual Django urlconf.
        """
        fspath = request.META['PATH_TRANSLATED']
        assert isfile(fspath), "This handler only serves files."
        request.urlconf = 'aspen.handlers.django_._' + self.filetype
        response = WSGIHandler.get_response(self, request)
        if 'Content-Type' not in response.headers:
            guess = mimetypes.guess_type(fspath, 'text/plain')[0]
            response.headers['Content-Type'] = guess
        return response
