import asyncio
import sys
import os
import logging

if __name__ == "__main__":
    sys.path.append(os.getcwd())

from utils.network import *
from .heros import HEROS, HEROS_DESCRIPTION

log = logging.getLogger(__name__)

class Client:
    def __init__(self, username, playerstatus, reader, writer):
        self.username = username
        self.playerstatus = playerstatus
        self.reader = reader
        self.writer = writer

    def __str__(self):
        return f"<Client {self.username!r}>"

    def __repr__(self):
        return str(self)

class PlayerPrivateStatus:
    pass

class Server:

    def __init__(self, owneruuid, ownerusername, loop):
        self.owneruuid = owneruuid
        self.clients = {}
        self._state = 'closed'
        self.loop = loop
        self.server = None

    async def start(self, port):
        try:
            self.server = await asyncio.start_server(
                self.gui_handle_new_client, "", port)
        except OSError as e:
            return e
        self.state = "waiting for owner"

    async def close(self):
        if self.state == 'closed':
            return
        if self.state != 'awaiting close':
            # wait for the server to be ready to be closed
            await asyncio.sleep(.1)
            return await self.close()
        self.state = "closed"
        for client in self.clients.values():
            client.writer.write_eof()
            await client.writer.drain()
            client.writer.close()
        if self.server:
            self.server.close()

    def setstate(self, newvalue):
        log.info(f'Server{{{newvalue}}}')
        self._state = newvalue

    state = property(lambda self: self._state, setstate)

    async def gui_handle_new_client(self, reader, writer):
        try:
            await self.handle_new_client(reader, writer)
        except ConnectionClosed as e:
            self.state = "Sending ClientLeft to other client"
            log.error(f"Client left: {e}")
            log.debug(f"Got {len(self.clients)} clients")
            # send message to other player
            for uuid, client in self.clients.items():
                if client.reader is e.reader:
                    # this is the client who left, don't send him anything
                    log.debug(f'skip {uuid} {client.username}')
                    continue
                log.debug(f"Send to client {uuid} {client.username} {client.writer}")
                await write(self.clients[uuid].writer, enc({
                    "kind": "client left", "username": client.username}))
            self.state = 'awaiting close'

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
        send 'Choose hero' to both the other player and the owner.
        """

        log.debug("Got brand new client!")

        fakeclient = Client(None, None, reader, writer)
        req = await read(fakeclient, 'uuid', 'username')

        uuid = req['uuid']
        username = req['username']
        self.clients[uuid] = Client(username, PlayerPrivateStatus(), reader,
                                    writer)

        if self.state == 'waiting for owner response':
            # don't accept any request from players when a request has already
            # been send to the owner
            # So, we tell the player the owner's busy.
            log.debug("Send owner busy with request.")
            await write(self.clients[uuid], {'kind': 'request state change',
                                             'state': 'declined',
                                             'reason': 'owner busy'})
            del self.clients[uuid]
            return

        if self.state == "waiting for player":
            # Here, we have a request from a player to join the onwer
            # the reader and the writer are the other player's, not the owner's
            log.debug(f"Send requests infos to owner {uuid!r} {username!r}")
            # send the uuid and username to the owner
            await write(self.clients[self.owneruuid], {'kind': 'new request',
                                                       'uuid': uuid,
                                                       'username': username})
            # feeds data because we were listening for nothing before
            # (not for nothing, just so that the server knows if the client
            # leaves)
            self.clients[self.owneruuid].reader.feed_data("\n")
            self.state = 'waiting for owner response'
            # wait for owner to reply
            res = await read(self.clients[self.owneruuid], 'accepted',
                             kind='request state change')
            log.debug(f"Response from owner {res!r}")
            # he said yes!
            if res['accepted'] is True:
                # to the client (the one that wanted to join)
                await write(self.clients[uuid], {
                    'kind': 'request state change',
                    'reason': None,
                    'accepted': True
                })
                return await self.hero_selection()
            else:
                if res['accepted'] is not False:
                    log.error("Got unexpected value for response to request"
                              f"{res['accepted']!r} (expecting a bool)")
                self.state = 'waiting for player'
                await write(self.clients[uuid], {'kind': 'request state change',
                                                 'accepted': False,
                                                 'reason': 'owner declined'})
                del self.clients[uuid]
                # start all over again
                self.loop.create_task(self.handle_new_client(reader, writer))
            return

        if req['kind'] != 'identification':
            raise ValueError(f"Got request of kind {req['kind']!r}, was "
                             "expecting 'identification'")
        # here, state must be 'waiting for owner'
        if uuid == self.owneruuid:
            self.state = "waiting for player"
            await write(self.clients[uuid], {
                'kind': 'identification state change',
                'state': 'success'
            })
            await read(self.clients[self.owneruuid])
        else:
            log.warning(f"Got fake request pretenting to be owner "
                        f"{uuid!r} {username!r}")
            await write(self.clients[uuid], {
                'kind': 'identification state change',
                'state': 'failed'
            })
            writer.write_eof()
            await writer.drain()
            writer.close()

    async def hero_selection(self):
        self.state = 'waiting for hero selection'
        await self.broadcast({
            'kind': 'next scene',
            'name': 'select hero',
            'heros_description': HEROS_DESCRIPTION
        })

    async def broadcast(self, *lines):
        for client in self.clients.values():
            await write(client, *lines)

    def __str__(self):
        return "<Server state={}>".format(self.state)

    def __repr__(self):
        return self.__str__()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    server = Server('dev', 'dev', loop)
    logging.basicConfig(level=logging.DEBUG, format='{asctime} {levelname:<5} {name} {message}', style='{')
    loop.create_task(server.start(9877))
    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()
