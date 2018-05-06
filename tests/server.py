import asyncio

from server import *
from utils.connection import *
from tests.constants import *
from tests.aut import *

class TestServer(Aut):

    async def before(self):
        self.server = Server('owner', self.loop)
        await self.server.start(PORT)

    async def after(self):
        await self.server.shutdown()
        await self.loop.shutdown_asyncgens()

    async def newconnection(self):
        return Connection(*(await asyncio.open_connection('localhost', PORT)))

    async def test_classic(self):
        """Test the server has a whole for a classic connection.

        That is, no one cancels anything at any time, the owner accepts
        the request, people choose an existing champion, etc.

        Here are the 3 things that are happening:
        - send something to server
        - expect response (from owner/other/both)
        - check server state
        and loop until we reach the game time (for now)
        """

        self.assertEqual(self.server.state, STATE_WAITING_OWNER)

        ownerco = await self.newconnection()
        await ownerco.write(kind='identification', uuid='owner',
                                username='owner username')

        res = await ownerco.read()
        self.assertEqual(res, {'kind': 'identification state change',
                               'state': 'accepted'})

        self.eventually(lambda: self.server.state, STATE_WAITING_REQUEST)

        # other player wants to join
        otherco = self.newconnection()
        await otherco.write(kind='new request', uuid='other',
                                username='other username')

        res = asyncio.gather(ownerco.read(), otherco.read())
        self.assertEqual(res[0], {'kind': 'new request',
                                  'from': 'other username'})
        self.assertEqual(res[1], {'kind': 'request state change',
                                  'state': 'waiting for owner response'})

        self.eventually(lambda: self.server.state, STATE_WAITING_REQUEST_REPLY)

        # send reply from owner
        await ownerco.write(kind='request state change', state='accepted')
        res = await otherco.read()
        self.assertEqual(res, {'kind': 'request state change',
                               'state': 'accepted'})

        self.eventually(lambda: self.server.state, STATE_HERO_SELECTION)

        for res in asyncio.gather(ownerco.read(), otherco.read()):
            self.assertEqual(res['kind'], 'select hero')
            self.assertIsInstance(res['heros'], dict)

        await ownerco.write(kind='chose hero', hero='adrian')
        await otherco.write(kind='chose hero', hero='adrian')

        self.eventually(lambda: self.server.state, STATE_GAME)

        for res in asyncio.gather(ownerco.read(), otherco.read()):
            self.assertEqual(res['kind'], 'game update')
            self.assertIsInstance(res['hero state'], dict)
            self.assertContains(res['hero state'], 'health', 'maxhealth',
                                'position', 'abilitiesCooldown', 'state',
                                'rotation')

