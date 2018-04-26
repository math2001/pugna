import asyncio
import logging
from collections import namedtuple
from utils.network import *

l = logging.getLogger(__name__)

Client = namedtuple('Client', 'username playerstatus reader writer')

class PlayerPrivateStatus:
    pass

class Server:

    def __init__(self, owneruuid, ownerusername, port):
        self.state = "waiting for owner"
        self.owneruuid = owneruuid
        self.clients = {}

        self.loop = asyncio.get_event_loop()
        self.server = self.loop.run_until_complete(asyncio.start_server(
            self.handle_new_client, "", port))

    def _state(self, newstate):
        l.debug("Change state to {!r}".format(newstate))
        self.state = newstate

    async def handle_new_client(self, reader, writer):
        """Handle new client depending on the state
        A request is composed of 2 lines: the uuid, and the username.

        If we are still waiting for the owner, we reject any request that isn't
        from the owner (which is defined based on the uuid)

        However, if the owner has already "logged in", we keep listening for 2
        lines (uuid and username) from an other player and send them to the
        owner. Then, we wait for the owner answer. We set the state to 'waiting
        for owner response' so that 2 other player can't set requests at the
        same time If it 'Accepted', we store the other player's information and
        send 'Choose champion' to both the other player and the owner.
        """

        uuid = (await readline(reader))
        username = (await readline(reader))

        if self.state == 'waiting for owner response':
            # don't accept any request from players when a request has already
            # been send to the owner
            # So, we tell the player the owner's busy.
            write(writer, "owner already requested")
            return

        if self.state == "waiting for player":
            # here, the reader and the writer are the other player's, not the
            # owner's
            await write(self.clients[self.owneruuid].writer, uuid, username)
            self._state('waiting for owner response')
            if await readline(self.clients[self.owneruuid].reader) \
                    == 'accepted':
                self.clients[uuid] = Client(username, reader, writer)
            else:
                self._state('waiting for player')
                await write(writer, "declined request.")

        # here, state must be 'waiting for owner'
        if uuid == self.owneruuid:
            self.clients[uuid] = Client(username, PlayerPrivateStatus(),
                                        reader, writer)
            self._state("waiting for player")
            await write(writer, "successful identification")
        else:
            await write(writer, "not owner. denied.")
            writer.close()

    def __str__(self):
        return "<Server state={}>".format(self.state)

    def __repr__(self):
        return self.__str__()
