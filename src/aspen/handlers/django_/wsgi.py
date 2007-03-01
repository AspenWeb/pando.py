from os.path import isfile

from django.core.handlers.wsgi import WSGIHandler


class WSGI(WSGIHandler):
    """This WSGI app serves PATH_TRANSLATED as a Django script or template.
    """

    filetype = '' # 'script' or 'template'

    def get_response(self, request):
        """Extend WSGIHandler.get_response to bypass usual Django urlconf.
        """
        assert ( isfile(request.META['PATH_TRANSLATED'])
               , "This handler only serves files." )
        request.urlconf = 'aspen.handlers.django_._' + self.filetype
        return WSGIHandler.get_response(self, request)
