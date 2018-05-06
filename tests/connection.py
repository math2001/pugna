# tests utils/connection.py

import unittest
import asyncio
from utils.connection import Connection
from tests.constants import *
import json

enc = json.JSONEncoder().encode
dec = json.JSONDecoder().decode

class TestConnection(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

        def on_new_client(r, w):
            self.server_r = r
            self.server_w = w

        self.server = self.loop.run_until_complete(asyncio.start_server(
            on_new_client, '', PORT, loop=self.loop))
        r, w = self.loop.run_until_complete(asyncio.open_connection(
            'localhost', PORT, loop=self.loop))
        self.connection = Connection(r, w)

    def tearDown(self):
        self.server_w.close()
        self.server.close()
        self.loop.run_until_complete(self.server.wait_closed())
        self.connection.w.close()
        self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        self.loop.close()

        self.server = None
        self.loop = None
        self.connection = None

    def test_read(self):
        args = (
            {'kind': 'test', 'arg': 'hello'},
            {'kind': 'hello'},
            {'kind': 'something', 'arg': 2, 'args': ['hello', 'world', 0.1]}
        )
        for arg in args:
            self.server_w.write((enc(arg) + '\n').encode('utf-8'))
            self.loop.run_until_complete(self.server_w.drain())
            result = self.loop.run_until_complete(self.connection.read())
            self.assertEqual(arg, result)

    def test_write(self):
        args = (
            {'kind': 'test', 'arg': 'hello'},
            {'kind': 'hello'},
            {'kind': 'something', 'arg': 2, 'args': ['hello', 'world', 0.1]}
        )
        for arg in args:
            self.loop.run_until_complete(self.connection.write(**arg))
            result = dec(self.loop.run_until_complete(self.server_r.readline())\
                         .decode('utf-8'))
            self.assertEqual(arg, result)

    def test_close(self):
        self.connection.close()
        # that's pretty much all we can do. From the documentation, is_closing
        # return True if the transport is closed OR if it's closing...
        self.assertTrue(self.connection.w.transport.is_closing())

        # the connection will be closed during the teardown as well, but that's
        # alright, because you can call close() more than once
