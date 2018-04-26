import asyncio
from collections import namedtuple

Client = namedtuple('Client', 'username playerstatus reader writer')

class PlayerPrivateStatus:
    pass

async def readline(reader):
    return (await reader.readerline()).decode('utf-8')

async def write(writer, *lines, drain=True):
    writer.write('\n'.join(lines).encode('utf-8'))
    if drain:
        await writer.drain()

class Server:

    def __init__(self, owneruuid, ownerusername, port):
        self.state = "waiting for owner"
        self.owneruuid = owneruuid
        self.clients = {}

        self.loop = asyncio.get_event_loop()
        self.server = self.loop.run_until_complete(asyncio.start_server(
            self.handle_new_client, "", port))

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

        uuid = await readline(reader).strip()
        username = await readline(reader).strip()

        if self.state == 'waiting for owner response':
            # don't accept any request from players when a request has already
            # been send to the owner
            # So, we tell the player the owner's busy.
            write(writer, "Owner already requested")
            return

        if self.state == "waiting for player":
            # here, the reader and the writer are the other player's, not the
            # owner's
            await write(self.clients[self.owneruuid].writer, uuid, username)
            self.state = 'waiting for owner response'
            if await readline(self.clients[self.owneruuid].reader) \
                    == 'Accepted':
                self.clients[uuid] = Client(username, reader, writer)
            else:
                self.state = 'waiting for player'
                await write(writer, "Declined request.")

        # here, state must be 'waiting for owner'
        if uuid == self.owneruuid:
            self.clients[uuid] = Client(username, PlayerPrivateStatus(),
                                        reader, writer)
            self.state = "waiting for player"
        else:
            write(writer, "Not owner. Denied.")
            writer.close()

    def __str__(self):
        return "<Server state={}>".format(self.state)

    def __repr__(self):
        return self.__str__()
