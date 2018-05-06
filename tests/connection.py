# tests utils/connection.py

import asyncio
from utils.connection import *
from tests.constants import *
from tests.aut import *
import json

enc = json.JSONEncoder().encode
dec = json.JSONDecoder().decode

class TestConnection(Aut):

    async def before(self):
        """Create new server every test"""

        def on_new_client(r, w):
            self.server_r = r
            self.server_w = w

        self.server = await asyncio.start_server(on_new_client, '', PORT)
        r, w = await asyncio.open_connection('localhost', PORT)
        self.connection = Connection(r, w)

    async def after(self):
        self.server_w.close()
        self.server.close()
        await self.server.wait_closed()
        self.connection.w.close()
        await self.loop.shutdown_asyncgens()

        self.server = None
        self.connection = None

    async def test_read(self):
        args = (
            {'kind': 'test', 'arg': 'hello'},
            {'kind': 'hello'},
            {'kind': 'something', 'arg': 2, 'args': ['hello', 'world', 0.1]}
        )
        for arg in args:
            self.server_w.write((enc(arg) + '\n').encode('utf-8'))
            await self.server_w.drain()
            result = await self.connection.read()
            self.assertEqual(arg, result)

    async def test_write(self):
        args = (
            {'kind': 'test', 'arg': 'hello'},
            {'kind': 'hello'},
            {'kind': 'something', 'arg': 2, 'args': ['hello', 'world', 0.1]}
        )
        for arg in args:
            await self.connection.write(**arg)
            result = dec((await self.server_r.readline()).decode('utf-8'))
            self.assertEqual(arg, result)

    async def test_aread(self):
        self.assertEqual(await self.connection.aread(), None)
        self.server_w.write((enc({'kind': 'message',
                                 'msg': 'hello world'}) + '\n').encode('utf-8'))
        await self.server_w.drain()
        await self.eventually(self.connection.aread, {"kind": "message",
                                                      "msg": "hello world"})

    def test_close(self):
        self.connection.close()
        # that's pretty much all we can do. From the documentation, is_closing
        # return True if the transport is closed OR if it's closing...
        self.assertTrue(self.connection.w.transport.is_closing())

        # the connection will be closed during the teardown as well, but that's
        # alright, because you can call close() more than once
