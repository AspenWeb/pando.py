from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen import json
from aspen.resources.dynamic_resource import DynamicResource


class JSONResource(DynamicResource):

    min_pages = 2
    max_pages = 2
    
    def compile_page(self, page):
        raise SyntaxError('JSON resources should only have logic pages')

    def process_raised_response(self, response):
        """Given a response, mutate it as needed.
        """
        self._process(response)

    def get_response(self, context):
        """Given a context dict, return a response object.
        """
        response = context['response']
        self._process(response)
        return response

    def _process(self, response):
        """Given a response object, mutate it for JSON.
        """
        if not isinstance(response.body, basestring):
            response.body = json.dumps(response.body)
        response.headers['Content-Type'] = self.website.media_type_json
