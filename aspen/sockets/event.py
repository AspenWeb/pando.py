from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

class Event(dict):

    def __init__(self, bytes):
        """Takes valid Socket.IO event JSON.
        """
        d = json.loads(bytes)
        self.update(d)
        self.name = d['name']
        self.args = d['args']
