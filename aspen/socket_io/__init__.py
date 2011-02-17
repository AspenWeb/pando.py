import hashlib
import logging
import time
import traceback
from struct import pack

try:
    import json
except ImportError:
    import simplejson as json

from aspen import simplates
from aspen.http import Response
from aspen.socket_io.transports import xhr_polling
from aspen.socket_io.utils import encode
from diesel import ConnectionClosed, first, fork, receive, send, until
from diesel.util.queue import Queue, QueueTimeout


log = logging.getLogger('aspen.socket_io')


def xhr_polling_handler(request, inq, outq):
    while True:
        try:
            xhr_request = inq.get(timeout=0.5)
        except QueueTimeout:
            pass
        else:
            log.info("handling xhr long-polling request")
            log.info(ws_request)
            try:
                simplates.handle(request)
            except Response, response:
                pass
            except:
                response = Response(500, traceback.format_exc())
            outq.put(response)

def handle(request):
    """Handle a request for a websocket.
    """
    if request.transport != 'xhr-polling':
        raise Response(404)

    org = request.headers.one('Origin')
    inq = Queue()
    outq = Queue()

    def wrap(request, inq, outq):
        handler(request, inq, outq)
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

