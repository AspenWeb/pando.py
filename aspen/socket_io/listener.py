class Listener(EventHub):

    def __init__(self, app):
        EventHub.__init__(self)
        self.app = app
        self.origins = '*:*'
        self.resource = 'socket.io'
        self.flashPolicyServer = true
        self.transports = [ 'websocket'
                          , 'flashsocket'
                          , 'htmlfile'
                          , 'xhr-multipart'
                          , 'xhr-polling'
                          , 'jsonp-polling'
                           ]
        self.transportOptions = {}
        
        self.clients = self.clientsIndex = {}
        self._clientCount = 0
        self._clientFiles = {}
        
        listeners = self.app.listeners('request')
        self.app.hub.removeAllListeners('request')
        
        self.app.hub.addListener('request', function(req, res){
            if (self.check(req, res)) return
            for (i = 0, len = listeners.length; i < len; i++){
                listeners[i].call(self, req, res)
            }
        })
        
        self.app.hub.addListener('upgrade', function(req, socket, head){
            if (!self.check(req, socket, true, head)){
                socket.end()
                socket.destroy()
            }
        })
        
        self.options.transports.forEach(function(name) {
            if (!(name in transports))
                transports[name] = require('./transports/' + name)
            if ('init' in transports[name]) transports[name].init(self)
        })

        log.info('socket.io ready - accepting connections')
    }

    def broadcast(self, message, except):
        for (i = 0, k = Object.keys(self.clients), l = k.length; i < l; i++){
            if (!except || ((typeof except == 'number' || typeof except == 'string') && k[i] != except)
                                    || (Array.isArray(except) && except.indexOf(k[i]) == -1)){
                self.clients[k[i]].send(message)
            }
        }
        return self
    }

    def check(self, req, res, httpUpgrade, head):
        path = url.parse(req.url).pathname, parts, cn
        if (path && path.indexOf('/' + self.options.resource) === 0){
            parts = path.substr(2 + self.options.resource.length).split('/')
            if (self._serveClient(parts.join('/'), req, res)) return true
            if (!(parts[0] in transports)) return false
            if (parts[1]){
                cn = self.clients[parts[1]]
                if (cn){
                    cn._onConnect(req, res)
                } else {
                    req.connection.end()
                    req.connection.destroy()
                    self.options.log('Couldnt find client with session id "' + parts[1] + '"')
                }
            } else {
                self._onConnection(parts[0], req, res, httpUpgrade, head)
            }
            return true
        }
        return false
    }

    def _serveClient(self, file, req, res):
        self = self
            , clientPaths = {
                    'socket.io.js': 'socket.io.js',
                    'lib/vendor/web-socket-js/WebSocketMain.swf': 'lib/vendor/web-socket-js/WebSocketMain.swf', // for compat with old clients
                    'WebSocketMain.swf': 'lib/vendor/web-socket-js/WebSocketMain.swf'
                }
            , types = {
                    swf: 'application/x-shockwave-flash',
                    js: 'text/javascript'
                }
        
        function write(path){
            if (req.headers['if-none-match'] == clientVersion){
                res.writeHead(304)
                res.end()
            } else {
                res.writeHead(200, self._clientFiles[path].headers)
                res.end(self._clientFiles[path].content, self._clientFiles[path].encoding)
            }
        }
        
        path = clientPaths[file]
        
        if (req.method == 'GET' && path !== undefined){
            if (path in self._clientFiles){
                write(path)
                return true
            }
            
            fs.readFile(__dirname + '/../../support/socket.io-client/' + path, function(err, data){
                if (err){
                    res.writeHead(404)
                    res.end('404')
                } else {
                    ext = path.split('.').pop()
                    self._clientFiles[path] = {
                        headers: {
                            'Content-Length': data.length,
                            'Content-Type': types[ext],
                            'ETag': clientVersion
                        },
                        content: data,
                        encoding: ext == 'swf' ? 'binary' : 'utf8'
                    }
                    write(path)
                }
            })
            
            return true
        }
        
        return false
    }

    def _onClientConnect(self, client):
        self.clients[client.sessionId] = client
        self.options.log('Client '+ client.sessionId +' connected')
        self.emit('clientConnect', client)
        self.emit('connection', client)
    }

    def _onClientMessage(self, data, client):
        self.emit('clientMessage', data, client)
    }

    def _onClientDisconnect(self, client):
        delete self.clients[client.sessionId]
        self.options.log('Client '+ client.sessionId +' disconnected')
        self.emit('clientDisconnect', client)
    }

    def _onConnection(self, transport, req, res, httpUpgrade, head):
        self.options.log('Initializing client with transport "'+ transport +'"')
        new transports[transport](self, req, res, self.options.transportOptions[transport], head)
    }




