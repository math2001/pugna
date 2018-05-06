import asyncio
import time
import logging
from utils.connection import *

log = logging.getLogger(__name__)

STATE_INIT = 'Initializing'
STATE_STARTING = 'Starting server'
STATE_WAITING_OWNER = 'Waiting for the owner to connect'
STATE_WAITING_REQUEST = 'Waiting for a player to join'
STATE_WAITING_REQUEST_REPLY = 'Waiting for the owner to reply'
STATE_HERO_SELECTION = 'Waiting for players to choose their hero'
STATE_GAME = "Playing!"
STATE_CLOSING = 'Closing'
STATE_CLOSED = 'Closed'


class Client:
    """Used to represent a client"""
    def __init__(self, name):
        self.name = name
        # the connection
        self.co = None
        # the status
        self.st = None

    def __str__(self):
        return f"<Client {self.name!r} c={self.c} s={self.s}>"

    def __repr__(self):
        return str(self)

class Server:

    def setstate(self, newvalue):
        log.info(f'Server{{{newvalue}}}')
        self._state = newvalue

    state = property(lambda self: self._state, setstate)

    def __init__(self, owneruuid, loop):
        """Doesn't start the server, just stores needed information

        We use the owneruuid to compare it the the first request we get (to know
        it it's the owner)"""

        self.state = STATE_INIT

        self.loop = loop

        self.owneruuid = owneruuid

        self.server = None
        # the player who hosts the game
        self.owner = Client("owner")
        # the player who joins the game
        self.other = Client("other")

        self.task_gameloop = None

        self.new_connections = []

    async def start(self, port):
        def new_co(r, w):
            log.debug("Got new connection")
            self.new_connections.append(Connection(r, w))

        self.state = STATE_STARTING
        self.server = await asyncio.start_server(new_co, "localhost", port)

        self.state = STATE_WAITING_OWNER
        self.task_gameloop = self.loop.create_task(self.gameloop())

    async def shutdown(self):
        """Closes the connections and close the server"""
        self.state = STATE_CLOSING
        if self.owner.co is not None:
            self.owner.co.close()
        if self.other.co is not None:
            self.other.co.close()

        self.server.close()
        await self.server.wait_closed()
        self.task_gameloop.cancel()
        self.state = STATE_CLOSED

    async def handle_new_connection(self, co):
        if self.state == STATE_WAITING_OWNER:
            res = await co.aread()
            if not res:
                return
            if res['kind'] != 'identification':
                raise NotImplementedError("Reply with error and close")
            if res['uuid'] != self.owneruuid:
                raise NotImplementedError("Reply with 'liar!' and close")
            self.owner.co = co

    async def gameloop(self):

        last = time.time()
        while self.state not in (STATE_CLOSING, STATE_CLOSED):
            dt = time.time() - last
            last = time.time()

            await asyncio.sleep(.05)

            if self.state in (STATE_WAITING_OWNER, STATE_WAITING_REQUEST):
                for co in self.new_connections:
                    await self.handle_new_connection(co)
