import asynctest
import asyncio

from server import *
from utils.connection import *
from tests.constants import *

def timeout(secs=TIMEOUT):
    def decorator(fn):
        async def wrapper(self, *args, **kwargs):
            try:
                return await asyncio.wait_for(fn(self, *args, **kwargs),
                                              timeout=secs)
            except asyncio.TimeoutError as e:
                return self.fail(f'Timeout ({secs}s): {fn}')
        return wrapper
    return decorator

class TestServer(asynctest.TestCase):

    async def setUp(self):
        self.server = Server('owner', self.loop)
        await self.server.start(PORT)

    async def tearDown(self):
        await self.server.shutdown()
        await self.loop.shutdown_asyncgens()

    async def eventually(self, obj, attr, value, x=10, wait=0.1):
        """Tests x times if the attribute is equal to value, awaiting a certain
        amount of time.
        """
        for _ in range(x):
            if getattr(obj, attr, None) == value:
                return True
            await asyncio.sleep(wait)
        self.fail(f"{obj.__class__.__name__!r} attribute {attr!r} hasn't been "
                  f"set to {value!r}. Got {getattr(obj, attr, None)!r}")

    async def newconnection(self):
        return Connection(*(await asyncio.open_connection('localhost', PORT)))

    @timeout()
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
        await ownerco.write(kind='identification', by='owner', uuid='owner',
                                username='owner username')

        res = await ownerco.read()
        self.assertEqual(res, {'kind': 'identification state change',
                               'state': 'accepted'})

        self.eventually(self.server, 'state', STATE_WAITING_REQUEST)

        # other player wants to join
        otherco = self.newconnection()
        await otherco.write(kind='new request', uuid='other',
                                username='other username')

        res = asyncio.gather(ownerco.read(), otherco.read())
        self.assertEqual(res[0], {'kind': 'new request',
                                  'from': 'other username'})
        self.assertEqual(res[1], {'kind': 'request state change',
                                  'state': 'waiting for owner response'})

        self.eventually(self.server, 'state', STATE_WAITING_REQUEST_REPLY)

        # send reply from owner
        await ownerco.write(kind='request state change', state='accepted')
        res = await otherco.read()
        self.assertEqual(res, {'kind': 'request state change',
                               'state': 'accepted'})

        self.eventually(self.server, 'state', STATE_HERO_SELECTION)

        for res in asyncio.gather(ownerco.read(), otherco.read()):
            self.assertEqual(res['kind'], 'select hero')
            self.assertIsInstance(res['heros'], dict)

        await ownerco.write(kind='chose hero', hero='adrian')
        await otherco.write(kind='chose hero', hero='adrian')

        self.eventually(self.server, 'state', STATE_GAME)

        for res in asyncio.gather(ownerco.read(), otherco.read()):
            self.assertEqual(res['kind'], 'game update')
            self.assertIsInstance(res['hero state'], dict)
            self.assertContains(res['hero state'], 'health', 'maxhealth',
                                'position', 'abilitiesCooldown', 'state',
                                'rotation')

