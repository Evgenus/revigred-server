import asyncio
import json

from autobahn.asyncio.websocket import (
    WebSocketServerProtocol,
    WebSocketServerFactory,
    )

class ServerProtocol(WebSocketServerProtocol):
    def onConnect(self, request):
        self.client = self.model.create_new_user()
        self.client.connect(self)
        self.logger.debug("Client connecting: {0}", request.peer)

    @asyncio.coroutine
    def onOpen(self):
        self.client.channel_opened()

    @asyncio.coroutine
    def onMessage(self, payload, isBinary):
        if isBinary:
            pass
        else:
            message = json.loads(payload.decode('utf8'))
            self.logger.debug("Text message received from {0}: {1}", self.client.name, payload.decode('utf8'))
            name, args, kwargs = message
            func = getattr(self.client, "on_" + name, None)
            func(*args, **kwargs)

    def onClose(self, wasClean, code, reason):
        self.client.disconnect()
        self.logger.debug("WebSocket connection closed: {0}", reason)

    def sendMessage(self, message):
        data = json.dumps(message).encode("utf-8")
        super().sendMessage(data, False)

class ServerFactory(WebSocketServerFactory):
    protocol = ServerProtocol

    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop("model")
        self.logger = kwargs.pop("logger")
        super().__init__(*args, **kwargs)

    def __call__(self):
        proto = super().__call__()
        proto.model = self.model
        proto.logger = self.logger
        return proto