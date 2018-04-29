from json import JSONDecoder, JSONEncoder

dec = JSONDecoder().decode
enc = JSONEncoder().encode

class CommunicationClosed(Exception):

    def __init__(self, msg, client):
        self.msg = msg
        self.client = client

async def read(client, *requiredkeys, kind=None):
    """Checks if a req has the required keys, and reply with an error and
    raises an exception. Otherwise, it simply returns the request
    clients just needs to have a reader and writer
    """
    res = (await client.reader.readline()).decode('utf-8')
    if not res:
        raise CommunicationClosed(f"Client {client} left.", client)
    res = dec(res)
    if not isinstance(res, dict) \
        or not all(k in res for k in requiredkeys + ('kind', )):
        await write(client.writer, {'kind': 'error', 'from': 'client',
                                    'reason': 'invalid informations',
                                    'requiredkeys': requiredkeys})
        raise ValueError("Got invalid informations")
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
