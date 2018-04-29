from json import JSONDecoder, JSONEncoder

dec = JSONDecoder().decode
enc = JSONEncoder().encode

class ConnectionClosed(Exception):

    def __init__(self, msg, reader):
        self.msg = msg
        self.reader = reader

async def read(client, *requiredkeys, kind=None):
    """Checks if a req has the required keys, and reply with an error and
    raises an exception. Otherwise, it simply returns the request
    clients just needs to have a reader and writer
    """
    requiredkeys += ('kind', )
    res = (await client.reader.readline()).decode('utf-8')
    if not res:
        raise ConnectionClosed(f"Client {client.reader} left.", client.reader)
    res = dec(res)
    if not isinstance(res, dict) \
        or not all(k in res for k in requiredkeys):
        reskeys = res.keys() if isinstance(res, dict) else res
        await write(client, {'kind': 'error', 'from': 'client',
                             'reason': 'invalid informations',
                             'requiredkeys': requiredkeys})
        raise ValueError("Got invalid informations (expected all of "
                         f"{requiredkeys} of kind {kind!r}, got {reskeys!r}")
    if kind is not None and res['kind'] != kind:
        raise ValueError(f"Invalid kind for the reply. Got {res['kind']!r}, "
                         f"expetected {kind!r}")
    return res

async def write(client, msg, drain=True):
    """Client needs to have a reader and a writer"""
    client.writer.write((enc(msg) + '\n').encode('utf-8'))
    if drain:
        await client.writer.drain()

def matches(d, *keys):
    return
