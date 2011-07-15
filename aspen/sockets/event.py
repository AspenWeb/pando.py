class Event(dict):

    def __init__(self, bytes):
        """Takes valid Socket.IO event JSON.
        """
        d = json.loads(bytes)
        self.update(d)
        self.name = d['name']
        self.args = d['args']
