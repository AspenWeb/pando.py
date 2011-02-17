class WebSocketDisconnect(object):
    pass


def web_socket_handler(request, inq, outq):
    while True:
        try:
            ws_request = inq.get(timeout=0.5)
        except QueueTimeout:
            pass
        else:
            log.info("handling websocket request")
            log.info(ws_request)
            try:
                simplates.handle(request)
            except Response, response:
                pass
            except:
                response = Response(500, traceback.format_exc())
            outq.put(response)

def get_handshake(request):
    """Given a Request, return a handshake string.
    """
    ws_location = "ws://localhost" + request.path
    if request.headers.has('Sec-WebSocket-Key1'):
        protocol = request.headers.one('Sec-WebSocket-Protocol')
        key1 = request.headers.one('Sec-WebSocket-Key1')
        key2 = request.headers.one('Sec-WebSocket-Key2')
        key3 = receive(8)
        num1 = int(''.join(c for c in key1 if c in '0123456789'))
        num2 = int(''.join(c for c in key2 if c in '0123456789'))
        assert num1 % key1.count(' ') == 0
        assert num2 % key2.count(' ') == 0
        final = pack('!II8s', num1 / key1.count(' '), num2 / key2.count(' '), key3)
        out = (
'''HTTP/1.1 101 Web Socket Protocol Handshake\r\n
Upgrade: WebSocket\r\n
Connection: Upgrade\r\n
Sec-WebSocket-Origin: %s\r\n
Sec-WebSocket-Location: %s\r\n
'''% (org, ws_location))
        if protocol is not None:
            out += "Sec-WebSocket-Protocol: %s\r\n" % (protocol,)
        out += "\r\n"
        out += hashlib.md5(final).digest()
    else:
        out = (
'''HTTP/1.1 101 Web Socket Protocol Handshake\r
Upgrade: WebSocket\r
Connection: Upgrade\r
WebSocket-Origin: %s\r
WebSocket-Location: %s\r
WebSocket-Protocol: diesel-generic\r
\r
''' % (org, ws_location))

    return out


def websockets(request):
    """Abortive attempt to get websockets working.
    """
    org = request.headers.one('Origin')
    inq = Queue()
    outq = Queue()

    def wrap(request, inq, outq):
        web_socket_handler(request, inq, outq)
        outq.put(WebSocketDisconnect())
    fork(wrap, request, inq, outq)

    while True:
        try:
            log.debug("trying websocket thing")
            typ, val = first(receive=1, waits=[outq.wait_id])
            log.debug(typ)
            log.debug(val)
            if typ == 'receive':
                assert val == '\x00'
                val = until('\xff')[:-1]
                if val == '':
                    inq.put(WebSocketDisconnect())
                else:
                    inq.put(request)
            else:
                try:
                    v = outq.get(waiting=False)
                except QueueEmpty:
                    pass
                else:
                    if type(v) is WebSocketDisconnect:
                        send('\x00\xff')
                        break
                    else:
                        send('\x00%s\xff' % response.to_http(request.version))

        except ConnectionClosed:
            inq.put(WebSocketDisconnect())
            raise ConnectionClosed("remote disconnected")

