import unittest
import asyncio
import os
from server import *
# we don't import it to test it, but to use it
from utils.connection import Connection
from tests.constants import *

class TestServer(unittest.TestCase):

    def newconnection(self, host, port):
        return Connection(*asyncio.wait_for(
            asyncio.open_connection(host, port, loop=self.loop), None,
            loop=self.loop))

    def assertContains(self, obj, *keys):
        for k in keys:
            if k not in obj:
                self.fail(f"{obj!r} doesn't contain {key!r}")

    def arun(self, coro):
        """Run asynchronously"""
        return self.loop.run_until_complete(coro)

    def eventually(self, obj, attr, value, x=10, wait=0.1):
        """Tests x times if the attribute is equal to value, awaiting a certain
        amount of time.
        """
        for _ in range(x):
            if getattr(obj, attr, None) == value:
                return True
            self.arun(asyncio.sleep(wait))
        self.fail(f"{obj.__class__.__name__!r} attribute {attr!r} hasn't been "
                  f"set to {value!r}. Got {getattr(obj, attr, None)!r}")

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        self.server = Server('owner', self.loop)
        self.arun(self.server.start(PORT))

    def test_classic(self):
        return self.arun(asyncio.wait_for(self.atest_classic(), TIMEOUT,
                                          loop=self.loop))

    async def atest_classic(self):
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

        ownerco = self.newconnection('localhost', PORT)
        self.arun(ownerco.write(kind='identification', by='owner', uuid='owner',
                                username='owner username'))

        res = self.arun(ownerco.read())
        self.assertEqual(res, {'kind': 'identification state change',
                               'state': 'accepted'})

        self.eventually(self.server, 'state', STATE_WAITING_REQUEST)

        # other player wants to join
        otherco = self.newconnection('localhost', PORT)
        self.arun(otherco.write(kind='new request', uuid='other',
                                username='other username'))

        res = asyncio.gather(ownerco.read(), otherco.read())
        self.assertEqual(res[0], {'kind': 'new request',
                                  'from': 'other username'})
        self.assertEqual(res[1], {'kind': 'request state change',
                                  'state': 'waiting for owner response'})

        self.eventually(self.server, 'state', STATE_WAITING_REQUEST_REPLY)

        # send reply from owner
        self.arun(ownerco.write(kind='request state change', state='accepted'))
        res = self.arun(otherco.read())
        self.assertEqual(res, {'kind': 'request state change',
                               'state': 'accepted'})

        self.eventually(self.server, 'state', STATE_HERO_SELECTION)

        for res in asyncio.gather(ownerco.read(), otherco.read()):
            self.assertEqual(res['kind'], 'select hero')
            self.assertIsInstance(res['heros'], dict)

        self.arun(ownerco.write(kind='chose hero', hero='adrian'))
        self.arun(otherco.write(kind='chose hero', hero='adrian'))

        self.eventually(self.server, 'state', STATE_GAME)

        for res in asyncio.gather(ownerco.read(), otherco.read()):
            self.assertEqual(res['kind'], 'game update')
            self.assertIsInstance(res['hero state'], dict)
            self.assertContains(res['hero state'], 'health', 'maxhealth',
                                'position', 'abilitiesCooldown', 'state',
                                'rotation')

