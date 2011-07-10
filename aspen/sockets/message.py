from aspen import json, Response


RESERVED_EVENTS = [ 'message'
                  , 'connect'
                  , 'disconnect'
                  , 'open'
                  , 'close'
                  , 'error'
                  , 'retry'
                  , 'reconnect'
                   ]


class Message(object):
    """Model a Socket.IO message.
    """

    def __init__(self, type_=0, id='', endpoint='', data=''):
        self.type = type_
        self.id = id
        self.endpoint = endpoint
        self.data = data

    @classmethod
    def from_bytes(cls, bytes):
        parts = bytes.split(':', 3)
        if len(parts) != 4:
            raise Response(400, "Malformed message: %s" % bytes)
        return cls(*parts)

    def __str__(self):
        data = self.data
        if self.type in (4, 5):
            data = json.dumps(data)
        return ":".join([ str(self.type)
                        , self.id
                        , self.endpoint
                        , data
                         ])

    # type
    # ====

    __type = 0

    def _get_type(self):
        return self.__type

    def _set_type(self, type_):
        try:
            type_ = int(type_)
            assert type_ in range(9)
        except (ValueError, AssertionError), exc:
            raise Response(400, "Message type not in 0..8: %s" % type_)
        self.__type = type_

    type = property(_get_type, _set_type)


    # data
    # ====

    __data = ''

    def _get_data(self):
        return self.__data

    def _set_data(self, data):
        if self.type == 4:              # json
            data = json.loads(data)
        elif self.type == 5:            # event
            data = json.loads(data)
            if 'name' not in data:
                raise Response(400, "Event message must have 'name' key.")
            if 'args' not in data:
                raise Response(400, "Event message must have 'args' key.")
            if data['name'] in RESERVED_EVENTS:
                raise Response( 400
                              , "Event name is reserved: %s." % data['name']
                               )
        self.__data = data

    data = property(_get_data, _set_data)

