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
STATE_GAME = "Game"
STATE_CLOSING = 'Closing'
STATE_CLOSED = 'Closed'

def handle_exception(fut):
    try:
        exc = fut.exception()
    except asyncio.CancelledError:
        return
    fut.result()

def new_hero(name):
    """Fake thing to create a hero"""
    return f"A brand new hero answering to the name of {name}"

class Client:
    """Used to represent a client"""
    def __init__(self, name):
        # the name is just used for debugging
        self.name = name
        # the connection
        self.co = None
        # the status
        self.st = None

        self.username = None
        self.uuid = None

    def __str__(self):
        return f"<Client {self.name!r} co={self.co} st={self.st}>"

    def __repr__(self):
        return str(self)

class Server:

    def setstate(self, newvalue):
        log.debug(f'Server{{{newvalue}}}')
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
            log.debug("Got new connection")
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

        Note that this method is called from the game loop. It isn't "attached"
        to the client or anything
        """

        # if we have no pending connection, and there are some connections to
        # handle, then we set the pending connection to the first connection
        if self.pending is None and len(self.new_connections) > 0:
            self.pending = self.new_connections.pop(0)
            log.debug(f"Managing new connection: {self.pending}")

        # we have every client nice and ready, why bother?
        if self.owner.co and self.other.co and self.pending:
            log.debug(f"Reject pending connection {self.pending} (enough "
                      "clients)")
            await self.pending.write(kind='request state change',
                                     state='refused by server')
            self.pending.close()
            self.pending = None
            return

        # non blocking read
        if self.pending:
            res = self.pending.aread()

        # haven't finished reading from the connection or there is no pending
        # connection. We'll check during the next iteration
        if not self.pending or not res:
            return

        if self.state == STATE_WAITING_OWNER:

            if res['kind'] != 'identification':
                raise NotImplementedError("Reply with error and close")

            if res['uuid'] != self.owneruuid:
                await self.pending.write(kind='identification state change',
                                         state='refused',
                                         reason='invalid uuid')
                self.pending.close()
                self.pending = None
                return

            await self.pending.write(kind='identification state change',
                                     state='accepted')

            self.owner.co = self.pending
            if 'by' not in res or 'uuid' not in res:
                raise NotImplementedError(f"need 'by' and 'uuid' in {res}")

            self.owner.username = res['by']
            self.owner.uuid = res['uuid']

            log.debug(f'Got owner: {self.owner}')
            self.pending = None
            self.state = STATE_WAITING_REQUEST

        elif self.state == STATE_WAITING_REQUEST:

            if res['kind'] != 'new request':
                raise NotImplementedError("Reply with error (expecting "
                                          "request) and close")
            if res['uuid'] == self.owneruuid:
                raise NotImplementedError("Reply with error (can't join own "
                                          "game)")
            # they both have the same username
            if res['by'] == self.owner.username:
                await self.pending.write(kind='request state change',
                                         state='refused',
                                         reason='username taken')
                self.pending.close()
                self.pending = None
                return
            self.other.co = self.pending
            if 'by' not in res or 'uuid' not in res:
                raise NotImplementedError(f"Need 'by' and 'uuid' in {res}")
            self.other.username = res['by']
            self.other.uuid = res['uuid']
            self.pending = None
            log.debug(f'Got other: {self.other}')
            # send request to owner, and confirmation to the other
            await asyncio.gather(
                self.owner.co.write(kind='new request', by=self.other.username),
                self.other.co.write(kind='request state change',
                                    state='waiting for owner response'))
            # note that this doesn't mean that the other player is accepted
            # the owner will decide that
            self.state = STATE_WAITING_REQUEST_REPLY

    async def handle_requests(self):
        if self.state not in (STATE_WAITING_REQUEST_REPLY, ):
            return
        res = self.owner.co.aread()
        if not res:
            return
        if res['kind'] != 'request state change':
            raise NotImplementedError(f"Expected kind to be 'request state "
                                      f"change', got {res['kind']!r} instead")
        if res['state'] == 'accepted':
            await self.other.co.write(kind='request state change',
                                      state='accepted')
            self.state = STATE_HERO_SELECTION
            await self.broadcast(kind='select hero', heros={
                'cool name': 'cool story'})

        elif res['state'] == 'refused':
            # send refused and close
            await self.other.co.write(kind='request state change',
                                      state='refused')
            self.other.co.close()
            self.other.co = None
            self.state = STATE_WAITING_REQUEST
        else:
            raise NotImplementedError("Handle invalid state for request")

    async def broadcast(self, *args, **kwargs):
        await asyncio.gather(self.owner.co.write(*args, **kwargs),
                             self.other.co.write(*args, **kwargs))

    async def handle_hero_selection(self):
        if self.state != STATE_HERO_SELECTION:
            return

        for client in (self.owner, self.other):
            res = client.co.aread()
            if not res:
                continue
            if res['kind'] != 'chose hero':
                raise NotImplementedError("Invalid kind for hero selection. "
                                          f"Got {res['kind']!r} instead of "
                                          "'chose hero'")
            client.st = new_hero(res['hero'])

        if self.owner.st and self.other.st:
            self.state = STATE_GAME

    async def handle_game(self):
        """Game on!"""
        if self.state != STATE_GAME:
            return

    async def gameloop(self):
        last = time.time()
        while self.state not in (STATE_CLOSING, STATE_CLOSED):
            dt = time.time() - last
            last = time.time()

            await asyncio.sleep(.05)

            # quick note: we could call these functions in any order, since they
            # don't block the loop in any way, everything is based on the state
            # of the server
            await self.handle_new_connections()
            await self.handle_requests()
            await self.handle_hero_selection()
            await self.handle_game()

