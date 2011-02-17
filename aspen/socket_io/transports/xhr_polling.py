from aspen.socket_io import client, utils


class XhrPolling(client.Client):

    def __init__(self):
        client.Client.__init__(self)
        self.timeout = None # no heartbeats
        self.closeTimeout = 8000
        self.duration = 20000

    def _onConnect(self, req, res):
        body = ''
        if req.method == 'GET':
            Client.prototype._onConnect.apply(self, [req, res])
            def foo():
                self._write('')
            self._closeTimeout = setTimeout(foo, self.options.duration)
            self._payload()
                
        else:
            assert req.method == 'POST'

            def on_body(message):
                body += message
            req.addListener('data', on_body)

            def on_end():
                headers = {'Content-Type': 'text/plain'}
                if (req.headers.origin):
                    if (self._verifyOrigin(req.headers.origin)):
                        headers.set('Access-Control-Allow-Origin', '*')
                        if (req.headers.cookie):
                            headers.set( 'Access-Control-Allow-Credentials'
                                       , 'true'
                                        )
                    else:
                        raise Response(401)
                try:
                    # optimization: just strip first 5 characters here?
                    msg = qs.parse(body)
                    self._onMessage(msg.data)
                except:
                    pass
    
                raise Response(200, "ok", headers)

            req.addListener('end', on_end)

    def _onClose(self):
        if (self._closeTimeout):
            clearTimeout(self._closeTimeout)
        return Client.prototype._onClose.call(self)
    
    def _write(self, message):
        if (self._open):
            headers = { 'Content-Type': 'text/plain; charset=UTF-8'
                      , 'Content-Length': len(message)
                       }
            # https://developer.mozilla.org/En/HTTP_Access_Control
            if (self.request.headers.origin and self._verifyOrigin(self.request.headers.origin)):
                headers.set('Access-Control-Allow-Origin', self.request.headers.origin)
                if (self.request.headers.cookie):
                    headers.set('Access-Control-Allow-Credentials', 'true')

            self._onClose()
            raise Response(200, message, headers)
