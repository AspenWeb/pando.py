from aspen import json
from aspen.resources.dynamic_resource import DynamicResource


class JSONResource(DynamicResource):

    min_pages = 2
    max_pages = 2

    def compile_page(self, page, padding):
        """Given None, return None. JSON resources have no third page.
        """
        assert page is None, page  # sanity check
        return None

    def process_raised_response(self, response):
        """Given a response, return a response.
        """
        return self._process(response)

    def get_response(self, context):
        """Given a context dict, return a response object.
        """
        response = context['response']
        return self._process(response)

    def _process(self, response):
        """Given a response object, process it for JSON.
        """
        if not isinstance(response.body, basestring):
            response.body = json.dumps(response.body)
        response.headers['Content-Type'] = self.website.media_type_json
        return response
