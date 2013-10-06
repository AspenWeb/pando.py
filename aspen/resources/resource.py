from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class Resource(object):
    """This is a base class for both static and dynamic resources.
    """

    def __init__(self, website, fs, raw, media_type, mtime):
        self.website = website
        self.fs = fs
        self.raw = raw
        self.media_type = media_type
        self.mtime = mtime
