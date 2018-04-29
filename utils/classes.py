from json import JSONDecoder, JSONEncoder

dec = JSONDecoder().decode
enc = JSONEncoder().encode

class PlayerPrivateStatus:
    pass

class Connection:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

    async def read(self, *requiredkeys, kind=None):
        """Checks if a req has the required keys, and reply with an error and
        raises an exception. Otherwise, it simply returns the request
        clients just needs to have a reader and writer
        """
        requiredkeys += ('kind', )
        res = (await self.reader.readline()).decode('utf-8')
        if not res:
            raise ConnectionClosed(f"Client left.", self.reader)
        res = dec(res)
        if not isinstance(res, dict) or not all(k in res for k in requiredkeys):
            reskeys = res.keys() if isinstance(res, dict) else res
            await self.write(kind='error', by='client',
                             reason='invalid informations',
                             requiredkeys=requiredkeys)
            raise ValueError("Got invalid informations (expected all of "
                            f"{requiredkeys} of kind {kind!r}, got {reskeys!r}")
        if kind is not None and res['kind'] != kind:
            raise ValueError(f"Invalid kind for the reply. Got {res['kind']!r}, "
                            f"expetected {kind!r}")
        return res

    async def write(self, **kwargs):
        """Client needs to have a reader and a writer"""
        self.writer.write((enc(kwargs) + '\n').encode('utf-8'))
        await self.writer.drain()

    async def close(client):
        client.writer.write_eof()
        await client.writer.drain()
        client.writer.close()

    def __str__(self):
        return f"<Client {self.username!r}>"

    def __repr__(self):
        return str(self)


class ConnectionClosed(Exception):

    def __init__(self, msg, reader):
        self.msg = msg
        self.reader = reader
