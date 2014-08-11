"""
aspen.renderers.jsonp_dump
~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen import renderers
from aspen.renderers.json_dump import Renderer as JsonRenderer

import re

CALLBACK_RE = re.compile(r'[^_a-zA-Z0-9]')


class Renderer(JsonRenderer):
    def render_content(self, context):
        # get the jsonp callback
        qs = context['request'].line.uri.querystring
        callback = qs.get('callback', qs.get('jsonp', None))

        # get the json
        json = JsonRenderer.render_content(self, context)

        # return the json if no callback requested
        if callback is None:
            return json

        response = context['response']

        # jsonp requested; fix the content-type
        response.headers['Content-Type'] = 'application/javascript'

        # sanify/sanitize the callback by nuking invalid characters
        callback = CALLBACK_RE.sub('', callback)

        # return the wrapped json
        # (preceding comment block prevent a Rosetta-Flash based attack)
        return "/**/ " + callback + "(" + json + ");"


class Factory(renderers.Factory):
    Renderer = Renderer
