import asyncio
import traceback
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

def handle_exception(fut):
    if fut.exception():
        fut.result()


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

        # this is a pending connection. It hasn't been accepted as the
        # onwer/other yet, but we still need keep contact with him.
        # !! It's not a Client, but still just a Connection
        self.pending = None

        self.task_gameloop = None

        self.new_connections = []

    async def start(self, port):
        def new_co(r, w):
            log.info("Got new connection")
            self.new_connections.append(Connection(r, w))

        self.state = STATE_STARTING
        self.server = await asyncio.start_server(new_co, "localhost", port)

        self.state = STATE_WAITING_OWNER
        self.task_gameloop = self.loop.create_task(self.gameloop())
        # raise exception if one occurs. It doesn't do it automatically because
        # we store the task into a variable (self.task_gameloop). Thanks for the
        # answer to https://stackoverflow.com/a/27299160/6164984
        self.task_gameloop.add_done_callback(handle_exception)

    async def shutdown(self):
        """Closes the connections and close the server"""
        self.state = STATE_CLOSING
        if self.owner.co is not None:
            self.owner.co.close()
        if self.other.co is not None:
            self.other.co.close()

        if self.server:
            self.server.close()
            await self.server.wait_closed()
        if self.task_gameloop:
            self.task_gameloop.cancel()
        self.state = STATE_CLOSED

    async def handle_new_connections(self):
        """Handles new connections. Makes the match, and once it's done, reject
        every person who wants to join.

        This functions never blocks the execution to wait for something. For
        example, instead of using co.read(), we use co.aread() which returns
        None if we haven't finished reading yet.
        """

        if self.pending is None and len(self.new_connections) > 0:
            self.pending = self.new_connections.pop(0)
            log.info(f"Managing new connection: {self.pending}")

        if self.pending:
            res = await self.pending.aread()
        if not self.pending or not res:
            # haven't finished reading from the connection or there is no
            # pending connection. We'll check during the next iteration
            return

        if self.state == STATE_WAITING_OWNER:
            if res['kind'] != 'identification':
                raise NotImplementedError("Reply with error and close")
            if res['uuid'] != self.owneruuid:
                raise NotImplementedError("Reply with 'liar!' and close")

            await self.pending.write(kind='identification state change',
                                     state='accepted')
            self.owner.co = self.pending
            self.pending = None
            self.state = STATE_WAITING_REQUEST

        elif self.state == STATE_WAITING_REQUEST:
            return
            if res['kind'] != 'new request':
                raise NotImplementedError("Reply with error (expecting "
                                          "request) and close")
            if res['uuid'] == self.owneruuid:
                raise NotImplementedError("Reply with error (can't join own "
                                          "game)")
            # send request to owner, and confirmation to the other
            await asyncio.gather(
                self.owner.co.write(kind='new request', by=res['username']),
                self.other.co.write(kind='request state change',
                                    state='waiting for owner response'))
    async def gameloop(self):
        last = time.time()
        while self.state not in (STATE_CLOSING, STATE_CLOSED):
            dt = time.time() - last
            last = time.time()

            await asyncio.sleep(.05)

            await self.handle_new_connections()
