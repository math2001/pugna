import asyncio
import logging
from collections import namedtuple
from utils.network import *

l = logging.getLogger(__name__)

Client = namedtuple('Client', 'username playerstatus reader writer')

class PlayerPrivateStatus:
    pass

class Server:

    def __init__(self, owneruuid, ownerusername):
        self.owneruuid = owneruuid
        self.clients = {}
        self._state = 'closed'

    async def start(self, port):
        l.info("Start server")
        self._state = "waiting for owner"
        self.server = await asyncio.start_server(self.handle_new_client, "", port)

    async def close(self):
        self.state = "closed"
        self.server.close()
        for client in self.clients.values():
            client.writer.close()

    def setstate(self, newvalue):
        l.info("Change state to {!r}".format(newvalue))
        self._state = newvalue

    state = property(lambda self: self._state, setstate)

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
            l.debug("Send owner busy with request.")
            write(writer, "owner already requested")
            return

        if self.state == "waiting for player":
            # Here, we have a request from a player to join the onwer
            # the reader and the writer are the other player's, not the owner's
            l.debug(f"Send requests infos to owner {uuid!r} {username!r}")
            # send the uuid and username to the owner
            await write(self.clients[self.owneruuid].writer, uuid, username)
            self.state = 'waiting for owner response'
            # wait for owner to reply
            response = await readline(self.clients[self.owneruuid].reader) 
            l.debug(f"Response from owner {response!r}")
            if response == 'accepted':
                self.clients[uuid] = Client(username, PlayerPrivateStatus(),
                                            reader, writer)
                await write(writer, 'accepted')
            else:
                self.state = 'waiting for player'
                await write(writer, "declined")
            return

        # here, state must be 'waiting for owner'
        if uuid == self.owneruuid:
            l.debug(f"Got owner's infos: {uuid!r} {username!r}")
            self.clients[uuid] = Client(username, PlayerPrivateStatus(),
                                        reader, writer)
            self.state = "waiting for player"
            await write(writer, "successful identification")
        else:
            l.warning(f"Got fake request pretenting to be owner "
                       "{uuid!r} {username!r}")
            await write(writer, "not owner. denied.")
            writer.close()

    def __str__(self):
        return "<Server state={}>".format(self.state)

    def __repr__(self):
        return self.__str__()
