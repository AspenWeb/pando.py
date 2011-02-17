import urlparse

from aspen.socket_io import utils


class Client(object):
    """Represent a web browser that wants a socket.
    """

    timeout = 8000
    heartbeatInterval = 10000
    closeTimeout = 0

    def __init__(self, listener, req, res, options, head):
        self.listener = listener
        self.connections = 0
        self._open = False
        self._heartbeats = 0
        self.connected = False
        self.upgradeHead = head
        self._onConnect(req, res)

    def send(self, message):
        if ( not self._open 
           or not (  self.connection.readyState == 'open' 
                  or self.connection.readyState == 'writeOnly' 
                    )):
            return self._queue(message)
        self._write(encode(message))
        return self

    def broadcast(self, message):
        if self.sessionId is None:
            return self
        self.listener.broadcast(message, self.sessionId)
        return self

    def _onMessage(self, data):
        messages = decode(data)
        if (messages == False):
            return self.listener.options.log('Bad message received from client ' + self.sessionId)
        for frame in messages:
            frame = messages[i].substr(0, 3)
            if frame == '~h~':
                return self._onHeartbeat(messages[i].substr(3))
            else:
                assert frame == '~j~' # sanity check
                try:
                    messages[i] = JSON.parse(messages[i].substr(3))
                except:
                    messages[i] = {}
            self.emit('message', messages[i])
            self.listener._onClientMessage(messages[i], self)

    def _onConnect(self, req, res):
        self.request = req
        self.response = res
        self.connection = req.connection

        def on_end():
            self._onClose()
            if (self.connection):
                self.connection.destroy()
        self.connection.addListener('end', on_end)
        
        if (req):
            def on_error_req(err):
                req.end and req.end() or req.destroy and req.destroy()
            req.addListener('error', on_error_req)
            
            if (res):
                def on_error_res(err):
                    res.end and res.end() or res.destroy and res.destroy()
                res.addListener('error', on_error_res)

            def on_error(err):
                req.connection.end and req.connection.end() or req.connection.destroy and req.connection.destroy()
            req.connection.addListener('error', on_error_connection)
                    
            if (self._disconnectTimeout):
                clearTimeout(self._disconnectTimeout)

    def _payload(self):
        payload = []
        
        self.connections += 1
        self.connected = True
        self._open = True
        
        if (not self.handshaked):
            self._generateSessionId()
            payload.push(self.sessionId)
            self.handshaked = True
        
        payload = payload.concat(self._writeQueue or [])
        self._writeQueue = []

        if (payload.length):
            self._write(encode(payload))
        if (self.connections == 1):
            self.listener._onClientConnect(self)
        if (self.options.timeout):
            self._heartbeat()
        
    def _heartbeat(self):
        def heartbeat():
            self._heartbeats += 1
            self.send('~h~' + self._heartbeats)
            def timeout():
                self._onClose()
            self._heartbeatTimeout = setTimeout(timeout, self.timeout)

        self._heartbeatInterval = setTimeout(heartbeat, self.heartbeatInterval)
        
    def _onHeartbeat(self, h):
        if (h == self._heartbeats):
            clearTimeout(self._heartbeatTimeout)
            self._heartbeat()

    def _onClose(self, skipDisconnect):
        if (not self._open):
            return self
        if (self._heartbeatInterval):
            clearTimeout(self._heartbeatInterval)
        if (self._heartbeatTimeout):
            clearTimeout(self._heartbeatTimeout)
        self._open = False
        self.request = null
        self.response = null
        if (not skipDisconnect):
            if self.handshaked:
                self._disconnectTimeout = setTimeout( self._onDisconnect
                                                    , self.closeTimeout
                                                     )
            else:
                self._onDisconnect()

    def _onDisconnect(self):
        if (self._open):
            self._onClose(True)
        if (self._disconnectTimeout):
            clearTimeout(self._disconnectTimeout)
        self._writeQueue = []
        self.connected = False
        if (self.handshaked):
            self.emit('disconnect')
            self.listener._onClientDisconnect(self)
            self.handshaked = False

    def _queue(self, message):
        self._writeQueue = self._writeQueue or []
        self._writeQueue.push(message)
        return self

    def _generateSessionId(self):
        self.sessionId = Math.random().toString().substr(2)
        return self

    def _verifyOrigin(self, origin):
        origins = self.listener.options.origins
        if (origins.indexOf('*:*') != -1):
            return True
        if (origin): 
            try:
                parts = urlparse(origin)
                return (origins.indexOf(parts.host + ':' + parts.port) != -1 or
                        origins.indexOf(parts.host + ':*') != -1 or
                        origins.indexOf('*:' + parts.port) != -1)
            except:
                pass
        return False

