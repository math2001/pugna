import asyncio
import json
from constants import *

enc = json.JSONEncoder().encode
dec = json.JSONDecoder().decode

class ConnectionClosed(Exception):
    pass

class Connection:

    """Represents a connection with a server or a client

    It communicates using JSON objects only. Every messages has to contain a
    'kind' field
    """

    def __init__(self, reader, writer):
        self.w = writer
        self.r = reader
        self.state = 'open'
        self.rtask = None

        s = ':'.join(str(x) for x in self.w.get_extra_info('sockname')[:2])
        p = ':'.join(str(x) for x in self.w.get_extra_info('peername')[:2])
        self._path = f"{s} to {p}"

    async def read(self):
        """Reads from reader

        Can raise different errors:
            - ConnectionClosed: the connection was closed
            - ValueError: json couldn't be parsed
            - KeyError: message does not contain the 'kind' field
        """
        if self.state == 'closed':
            raise ConnectionClosed(f"{self} connection already closed")
        line = (await self.r.readline()).decode('utf-8')
        if '\n' not in line:
            self.state = 'closed'
            raise ConnectionClosed(f"{self} was closed")
        message = dec(line)
        if 'kind' not in message:
            raise KeyError(f"Message should contain a 'kind' field. Got "
                           f"{message}")
        return message

    async def write(self, **kwargs):
        """Writes on the writer"""
        if self.state == 'closed':
            raise ConnectionClosed(f"{self} writing to a closed connection")
        self.w.write((enc(kwargs) + '\n').encode('utf-8'))
        await self.w.drain()

    def aread(self):
        """Reads from reader using tasks

        Basically, you can call this as many times as you want, it'll read again
        only once the previous read has been done. It returns None the task
        isn't done, otherwise it returns the result"""
        if self.rtask is None:
            self.rtask = asyncio.ensure_future(self.read())
        elif self.rtask.done():
            res = self.rtask.result()
            self.rtask = None
            return res

        # otherwise, do nothing!

    def close(self):
        """Doesn't actually close the socket. Just orders it to close
        After a fair bit of googling, i came across this issue:
        https://github.com/python/asyncio/issues/141
        The problem being that there is now proper way of waiting for the socket
        to be closed *apart* from calling loop.shutdown_asyncgens(), which shuts
        *everything* down.

        TLDR: make sure you close loop.shutdown_asyncgens() before closing the
        loop (or exiting the program) so that we actually wait for the sockets
        to be closed.
        """
        self.w.write_eof()
        self.w.close()
        if self.rtask:
            self.rtask.cancel()

    def __repr__(self):
        return f"<Connection {self._path} state={self.state!r}>"

    def __str__(self):
        return repr(self)

