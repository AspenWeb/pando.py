"""
aspen.resources.resource
~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class Resource(object):
    """This is a base class for both static and dynamic resources.
    """

    def __init__(self, website, fs, raw, media_type, is_media_type_from_fs, mtime):
        self.website = website
        self.fs = fs
        self.raw = raw
        self.media_type = media_type
        self.is_media_type_from_fs = is_media_type_from_fs
        self.mtime = mtime
