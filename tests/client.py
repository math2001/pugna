# tests utils.client, not the client itself

import asyncio
import logging
from utils.connection import Connection
from utils.client import Client
from tests.aut import Aut
from constants import *

log = logging.getLogger(__name__)

class TestClient(Aut):

    async def before(self):
        self.clients = []
        def new_client(r, w):
            self.clients.append(Connection(r, w))
        self.server = await asyncio.start_server(new_client, 'localhost', PORT)
        self.client = await Client.new('localhost', PORT)

        self.assertEqual(len(self.clients), 1)

    async def after(self):
        self.server.close()
        await self.server.wait_closed()
        self.client.shutdown()

    async def test_successful_login(self):
        """Test successful login"""
        # this is the client from the server point of view
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
