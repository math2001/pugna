from json import JSONDecoder, JSONEncoder

dec = JSONDecoder().decode
enc = JSONEncoder().encode

class Connection:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.closed = False

    @staticmethod
    async def handle_dec(bytes, *requiredkeys, kind=None):
        requiredkeys += ('kind', )
        if not res:
            raise ConnectionClosed(f"Connection closed", self.reader)
        res = dec(res)
        if not isinstance(res, dict) or not all(k in res for k in requiredkeys):
            reskeys = res.keys() if isinstance(res, dict) else res
            await self.write(kind='error', by='client',
                             reason='invalid informations',
                             requiredkeys=requiredkeys)
            raise InvalidMessage("Got invalid informations (expected all of "
                            f"{requiredkeys} of kind {kind!r}, got {reskeys!r}")
        if kind is not None and res['kind'] != kind:
            raise InvalidMessage(f"Invalid kind for the reply. Got "
                                 f"{res['kind']!r}, expetected {kind!r}")
        return res

    async def read(self, *args, **kwargs):
        """Checks if a req has the required keys, and reply with an error and
        raises an exception. Otherwise, it simply returns the request.
        """
        res = await self.reader.readline(*args, **kwargs)
        return Connection.handle_dec(res)

    async def write(self, **kwargs):
        self.writer.write((enc(kwargs) + '\n').encode('utf-8'))
        await self.writer.drain()

    async def close(self):
        self.writer.write_eof()
        await self.writer.drain()
        self.writer.close()
        self.closed = True

    def __str__(self):
        return f"<Connection {'closed' if self.closed else 'open'}>"

    def __repr__(self):
        return str(self)


class ConnectionClosed(Exception):

    def __init__(self, msg, reader):
        self.msg = msg
        self.reader = reader

class InvalidMessage(Exception):
    pass
