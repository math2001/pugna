# tests utils.client, not the client itself

import asyncio
import logging
from utils.connection import Connection
from utils.client import Client
from tests.aut import Aut
from constants import *

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class TestClient(Aut):

    async def before(self):
        self.clients = []
        def new_client(r, w):
            self.clients.append(Connection(r, w))
        self.server = await asyncio.start_server(new_client, 'localhost', PORT)
        self.client = await Client.new('localhost', PORT)

        self.assertEqual(len(self.clients), 1)

    async def newconnection(self):
        """Opens a new raw connection to self.server"""
        return Connection(*(await asyncio.open_connection('localhost', PORT)))

    async def after(self):
        self.server.close()
        await self.server.wait_closed()
        self.client.shutdown()

    async def test_successful_login(self):
        """Test successful login"""
        # self.clients[0] is the server's connection with self.client
        server = self.clients[0]

        task = self.loop.create_task(self.client.login('username', 'uuid'))
        req = await server.read()
        self.assertEqual(req, {'kind': 'identification', 'by': 'username',
                               'uuid': 'uuid'})
        await server.write(kind='identification state change',
                           state='accepted')
        res = await task
        self.assertTrue(res.accepted)

    async def test_refused_login(self):
        """Test logging in with invalid ids"""
        server = self.clients[0]

        task = self.loop.create_task(self.client.login('username', 'uuid'))
        req = await server.read()
        self.assertEqual(req, {'kind': 'identification', 'by': 'username',
                               'uuid': 'uuid'})
        await server.write(kind='identification state change',
                           state='refused',
                           reason='owner refused')
        res = await task
        self.assertFalse(res.accepted)
        self.assertEqual(res.msg, 'owner refused')

    async def test_findplayer(self):
        """Waits for a player to request join"""
        server = self.clients[0]

        task = self.loop.create_task(self.client.findplayer())

        log.debug("send fake request from server, awaiting response")

        await server.write(kind='new request', by='somekid')

        # check if the owner (self.client) did recieve the request
        req = await task
        self.assertEqual(req.by, 'somekid')

    async def test_refuse_request(self):
        server = self.clients[0]

        task = self.loop.create_task(self.client.refuse_request())

        req = await server.read()
        self.assertEqual(req, {'kind': 'request state change',
                               'state': 'refused',
                               'reason': 'owner refused'})

    async def test_accept_request(self):
        server = self.clients[0]

        task = self.loop.create_task(self.client.accept_request())

        req = await server.read()
        self.assertEqual(req, {'kind': 'request state change',
                               'state': 'accepted'})

