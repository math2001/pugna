import asyncio
import logging

from utils.classes import *
from server.heros import HEROS_DESCRIPTION

log = logging.getLogger(__name__)

STATE_WAITING_OWNER = 'Waiting for the owner to connect'
STATE_WAITING_REQUEST = 'Waiting for a player to join'
STATE_WAITING_REQUEST_REPLY = 'Waiting for the owner to reply'
STATE_HERO_SELECTION = 'Waiting for players to choose their hero'
STATE_CLOSING = 'closing'
STATE_CLOSED = 'closed'

class Server:

    def __init__(self, owneruuid, loop):
        self.owneruuid = owneruuid
        self.loop = loop

        self._state = 'init'

        # both will be Connection(). The owner is the one who hosts the game
        # and the client is the one who joins the game
        self.owner = None
        self.player = None

        # these are clients who haven't identified yet. They are kept here
        # so that we can close them in case the server is shutdown
        self.anonymous_clients = []

        # these tasks are used to read both the player and the owner at the same
        # time (so we don't use await, which would block)
        self.player_task = None
        self.owner_task = None

    def setstate(self, newvalue):
        log.info(f'Server{{{newvalue}}}')
        self._state = newvalue

    state = property(lambda self: self._state, setstate)

    async def broadcast(self, *args, **kwargs):
        """Send messages to every client"""
        return await asyncio.wait((
            self.loop.create_task(self.owner.write(*args, **kwargs)),
            self.loop.create_task(self.player.write(*args, **kwargs))
        ))

    async def start(self, port):
        """Start the server and the game loop."""
        try:
            self.server = await asyncio.start_server(
                self.handle_new_client, "", port
            )
        except OSError as e:
            return e
        self.state = STATE_WAITING_OWNER
        self.loop.create_task(self.gameloop())

    async def shutdown(self):
        """Shutdown the owner's connection, the other client's, and then the
        server"""
        if self.state == STATE_CLOSED:
            return

        self.state = STATE_CLOSING

        if self.owner_task:
            self.owner_task.cancel()
        if self.player_task:
            self.player_task.cancel()

        if self.owner:
            await self.owner.close()

        if self.player:
            await self.player.close()

        for client in self.anonymous_clients:
            await client.close()

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        self.state = STATE_CLOSED

    async def new_client(self, writer, reader):
        """Handles a new client.

        All it does is change the state and store the clients. It doesn't start
        the game loop or anything (the game loop has to be independent of the
        clients. Remember, here, we're in a client's callback function).
        """

        try:
            self.handle_new_client(writer, reader)
        except ConnectionClosed as e:
            await client.close()
            log.info(f"Client {client} left")
        except InvalidMessage as e:
            await client.close()
            log.error(f"Invalid informations for identification. {e}")

    async def handle_new_client(self, writer, reader):

        client = Connection(writer, reader)

        if self.owner and self.player:
            await client.write(kind='request state change', state='declined',
                               reason='enough players for now')
            await client.close()
            return

        self.anonymous_clients.append(client)

        details = await client.read('uuid', 'username',
                                    kind='identification')
        self.anonymous_clients.pop()

        client.uuid = details['uuid']
        client.username = details['username']

        if self.state == STATE_WAITING_OWNER:
            # got someone pretending to be the owner. Let's check first, hey
            if client.uuid == self.owneruuid:
                self.owner = client
                await self.owner.write(kind='identification state change',
                                       state='success')
                self.state = STATE_WAITING_REQUEST
            else:
                log.error(f"{client} tried to connect as owner.")
                await self.owner.write(kind='identification state change',
                                       state='failed')

        elif self.state == STATE_WAITING_REQUEST:
            # got a request from a player (client)
            self.player = client
            await self.owner.write(kind='new request', uuid=self.player.uuid,
                             username=self.player.username)
            self.state = STATE_WAITING_REQUEST_REPLY
        else:
            log.critical(f"new client handler shouldn't get here ({client})")

    async def handle_player_request(self):
        """Handle a request once the owner has recieved it.

        Returns True if it was accepted, False otherwise"""
        req = await self.owner.read('state', kind='request state change')
        if req['state'] == 'accepted':
            await self.player.write(kind='request state change',
                                    state='accepted',
                                    reason=None)
            self.state = STATE_HERO_SELECTION

            # initiate hero selection
            await self.broadcast(kind='next scene data',
                                 heros_description=HEROS_DESCRIPTION)

            # these 2 tasks will be used by handle_hero_selection
            self.owner_task = self.loop.create_task(
                self.owner.read('name', kind='chose hero'))
            self.player_task = self.loop.create_task(
                self.player.read('name', kind='chose hero'))

            return True
        elif req['state'] == 'declined':
            await self.player.write(kind='request state change',
                                    state='declined',
                                    reason='owner declined')
            await self.player.close()
            self.player = None
            self.state = STATE_WAITING_REQUEST
        else:
            log.critical(f"Got unexpected state for 'request state change': "
                         f"{req['state']!r}")
        return False


    async def handle_hero_selection(self):
        # check for both players wheter they have chosen their champion and
        # send it to the other player
        if self.owner_task.done():
            await self.player.write(kind='other player ready',
                                    username=self.player.username)

        if self.player_task.done():
            await self.owner.write(kind='other player ready',
                                   username=self.owner.username)

        if self.player_task.done() and self.owner_task.done():
            await self.broadcast(kind='next scene', name='game')

    async def gameloop(self):
        """loops..."""
        while self.state != STATE_CLOSED:
            await asyncio.sleep(.5)
            if self.state in (STATE_WAITING_OWNER, STATE_WAITING_REQUEST):
                continue

            elif self.state == STATE_WAITING_REQUEST_REPLY:
                if not await self.handle_player_request():
                    continue # skip the rest of this loop

            elif self.state == STATE_HERO_SELECTION:
                if not await self.handle_hero_selection():
                    continue # as long as the players are choosing, we skip

