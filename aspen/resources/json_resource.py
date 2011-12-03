import datetime

from aspen import json
from aspen.resources.dynamic_resource import DynamicResource


class JSONResource(DynamicResource):

    min_pages = 2
    max_pages = 2

    def compile_third(self, one, two, three, padding):
        """Given None, return None. JSON resources have no third page.
        """
        assert three is None # sanity check
        return three 

    def compile_fourth(self, one, two, three, four, padding):
        """Given None, return None. Socket resources have no fourth page.
        """
        assert four is None # sanity check
        return four 

    def process_raised_response(self, response):
        """Given a response, return a response.
        """
        return self._process(response)
  
    def get_response(self, namespace):
        """Given a namespace dict, return a response object.
        """
        response = namespace['response']
        return self._process(response)

    def _process(self, response):
        """Given a response object, process it for JSON.
        """
        if not isinstance(response.body, basestring):
            response.body = json.dumps(response.body)
        response.headers.set('Content-Type', self.website.json_content_type)
        return response
