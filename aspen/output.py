class Output(object):
    body = media_type = charset = None

    def __init__(self, **kw):
        self.__dict__.update(kw)
