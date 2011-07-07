class Resource(object):
    """This is a base class for both static and dynamic resources.
    """

    def __init__(self, website, fs, raw, mimetype, modtime):
        self.website = website
        self.fs = fs
        self.raw = raw
        self.mimetype = mimetype
        self.modtime = modtime
