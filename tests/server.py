import asyncio

from server import *
from utils.connection import *
from constants import *
from tests.aut import *

class TestServer(Aut):

    async def identify(self, username, uuid):
        """Utils function to connect a client as the owner"""
        co = await self.newconnection()
        await co.write(kind='identification', by=username, uuid=uuid)
        return co

    async def request(self, username, uuid):
        """Utils function to connect a client as the other"""
        co = await self.newconnection()
        await co.write(kind='new request', by=username, uuid=uuid)
        return co

    async def before(self):
        self.server = Server('owner', self.loop)
        await self.server.start(PORT)

    async def after(self):
        await self.server.shutdown()
        await self.loop.shutdown_asyncgens()

    async def newconnection(self):
        co = Connection(*(await asyncio.open_connection('localhost', PORT)))
        log.debug(f"Create new connection {co!r}")
        return co

    async def test_classic(self):
        """Test the server's matchmaking has a whole for a classic connection.

        That is, no one cancels anything at any time, the owner accepts
        the request, people choose an existing champion, etc.

        Here are the 3 things that are happening:
        - send something to server
        - expect response (from owner/other/both)
        - check server state
        and loop until we reach the game time (for now)
        """

        self.assertEqual(self.server.state, STATE_WAITING_OWNER)

        # create owner connection
        ownerco = await self.newconnection()
        # log into the server
        await ownerco.write(kind='identification', uuid='owner',
                            by='owner username')

        res = await ownerco.read()
        self.assertEqual(res, {'kind': 'identification state change',
                               'state': 'accepted'})

        await self.eventually(lambda: self.server.state,
                              STATE_WAITING_REQUEST)

        # We create a new player and ask the owner to join
        otherco = await self.newconnection()
        await otherco.write(kind='new request', uuid='other',
                            by='other username')

        # check if the owner recieved the request, and if the other recieved the
        # confirmation (that his request had been sent)
        res = await asyncio.gather(ownerco.read(), otherco.read())
        self.assertEqual(res[0], {'kind': 'new request',
                                  'by': 'other username'})
        self.assertEqual(res[1], {'kind': 'request state change',
                                  'state': 'waiting for owner response'})

        await self.eventually(lambda: self.server.state,
                              STATE_WAITING_REQUEST_REPLY)

        # send reply from owner (he accepts it)
        await ownerco.write(kind='request state change', state='accepted')

        res = await otherco.read()
        self.assertEqual(res, {'kind': 'request state change',
                               'state': 'accepted'})

        await self.eventually(lambda: self.server.state, STATE_HERO_SELECTION)

        for res in await asyncio.gather(ownerco.read(), otherco.read()):
            self.assertEqual(res['kind'], 'select hero')
            self.assertIsInstance(res['heros'], dict)

        await ownerco.write(kind='chose hero', hero='adrian')
        await otherco.write(kind='chose hero', hero='adrian')

        await self.eventually(lambda: self.server.state, STATE_GAME)

        # stop testing up to here for now
        return

        for res in await asyncio.gather(ownerco.read(), otherco.read()):
            self.assertEqual(res['kind'], 'game update')
            self.assertIsInstance(res['hero state'], dict)
            self.assertContains(res['hero state'], 'health', 'maxhealth',
                                'position', 'abilitiesCooldown', 'state',
                                'rotation')

    async def test_wrong_owner(self):
        """Test the matchmaking where the owner sends in the wrong uuid"""

        self.assertEqual(self.server.state, STATE_WAITING_OWNER)

        owner = await self.newconnection()
        await owner.write(kind='identification', uuid='WRONG owner',
                          by='owner username')

        res = await owner.read()
        self.assertEqual(res, {'kind': 'identification state change',
                               'state': 'refused',
                               'reason': 'invalid uuid'})

        with self.assertRaises(ConnectionClosed):
            await owner.read()

        self.assertEqual(self.server.state, STATE_WAITING_OWNER)

        owner = await self.newconnection()
        # this time, we login with the right username
        await owner.write(kind='identification', uuid='owner',
                          by='owner username')

        res = await owner.read()
        self.assertEqual(res, {'kind': 'identification state change',
                               'state': 'accepted'})


    async def test_more_client(self):
        """Send an other request when there is already a owner and an other"""

        self.assertEqual(self.server.state, STATE_WAITING_OWNER)

        owner = await self.newconnection()
        await owner.write(kind='identification', uuid='owner',
                          by='owner username')

        self.assertEqual(await owner.read(),
                         {'kind': 'identification state change',
                          'state': 'accepted'})
        self.assertEqual(self.server.state, STATE_WAITING_REQUEST)

        # send request
        other1 = await self.newconnection()
        await other1.write(kind='new request', uuid='other1',
                           by='other1')

        self.assertEqual(await owner.read(), {'kind': 'new request',
                                              'by': 'other1'})
        # accept
        await owner.write(kind='request state change', state='accepted')

        res = await owner.read()
        self.assertEqual(res['kind'], 'select hero')

        self.assertEqual(self.server.state, STATE_HERO_SELECTION)

        # send in an other request
        other2 = await self.newconnection()
        await other2.write(kind='new request', uuid='other2', by='other2')
        # check the response
        res = await other2.read()
        self.assertEqual(res, {'kind': 'request state change',
                               'state': 'refused by server'})

        self.assertEqual(self.server.state, STATE_HERO_SELECTION)

    async def test_request_rejection(self):
        """Test handling of multiple request rejection by the owner"""

        self.assertEqual(self.server.state, STATE_WAITING_OWNER)

        owner = await self.newconnection()
        await owner.write(kind='identification', uuid='owner',
                          by='owner username')

        self.assertEqual(await owner.read(),
                         {'kind': 'identification state change',
                          'state': 'accepted'})
        self.assertEqual(self.server.state, STATE_WAITING_REQUEST)

        # first client who wants to join (refused)
        other1 = await self.newconnection()
        await other1.write(kind='new request', by='other 1', uuid='other1')
        self.assertEqual(await other1.read(), {
            'kind': 'request state change',
            'state': 'waiting for owner response'})

        self.assertEqual(await owner.read(), {'kind': 'new request',
                                              'by': 'other 1'})

        self.assertEqual(self.server.state, STATE_WAITING_REQUEST_REPLY)

        await owner.write(kind='request state change', state='refused')

        self.assertEqual(await other1.read(), {'kind': 'request state change',
                                               'state': 'refused',
                                               'reason': 'owner refused'})
        with self.assertRaises(ConnectionClosed):
            await other1.read()

        # second client who wants to join (refused)
        other2 = await self.newconnection()
        await other2.write(kind='new request', by='other 2', uuid='other2')
        self.assertEqual(await other2.read(),
                         {'kind': 'request state change',
                          'state': 'waiting for owner response'})
        self.assertEqual(await owner.read(), {'kind': 'new request',
                                              'by': 'other 2'})
        self.assertEqual(self.server.state, STATE_WAITING_REQUEST_REPLY)
        await owner.write(kind='request state change', state='refused')

        self.assertEqual(await other2.read(), {'kind': 'request state change',
                                               'state': 'refused',
                                               'reason': 'owner refused'})
        with self.assertRaises(ConnectionClosed):
            await other2.read()

        # third client who wants to join (accepted)
        other3 = await self.newconnection()
        await other3.write(kind='new request', by='other 3', uuid='other3')
        self.assertEqual(await other3.read(), {
            'kind': 'request state change',
            'state': 'waiting for owner response'})

        self.assertEqual(await owner.read(), {'kind': 'new request',
                                              'by': 'other 3'})

        self.assertEqual(self.server.state, STATE_WAITING_REQUEST_REPLY)

        await owner.write(kind='request state change', state='accepted')

        self.assertEqual(await other3.read(), {'kind': 'request state change',
                                               'state': 'accepted'})
        self.assertEqual(self.server.state, STATE_HERO_SELECTION)

    async def test_same_username(self):
        """Test handling of 2 different clients who have the same username"""

        owner = await self.identify('coolusername', 'owner')
        self.assertEqual(await owner.read(), {
            'kind': 'identification state change',
            'state': 'accepted'
        })

        other1 = await self.request('coolusername', 'other uuid')
        self.assertEqual(await other1.read(), {
            'kind': 'request state change',
            'state': 'refused',
            'reason': 'username taken'
        })

        self.assertEqual(self.server.state, STATE_WAITING_REQUEST)

        other2 = await self.request('anothercoolusername', 'other uuid')
        self.assertEqual(await owner.read(), {
            'kind': 'new request',
            'by': 'anothercoolusername'
        })
        await owner.write(kind='request state change')
        self.assertEqual(await other2.read(), {
            'kind': 'request state change',
            'state': 'waiting for owner response'
        })

        self.assertEqual(self.server.state, STATE_WAITING_REQUEST_REPLY)

