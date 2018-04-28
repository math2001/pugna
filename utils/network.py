from json import JSONDecoder

dec = JSONDecoder().decode
end = JSONEncoder().encode

class CommunicationClosed(Exception):

    def __init__(self, msg, client):
        self.msg = msg
        self.client = client

async def read(self, client, *requiredkeys):
    """Checks if a req has the required keys, and reply with an error and
    raises an exception. Otherwise, it simply returns the request
    """

    res = (await client.reader.readline()).decode('utf-8')
    if not res:
        raise CommunicationClosed(f"Client {client} left.", client)
    res = dec(res)
    if not isinstance(res, dict) \
        or not all(k in res for k in requiredkeys + ['kind']):
        await write(client.writer, {'kind': 'error', 'from': 'client',
                                    'reason': 'invalid informations',
                                    'requiredkeys': requiredkeys})
        raise ValueError("Got invalid informations")
    return res



async def write(writer, msg, drain=True):
    writer.write((enc(msg)).encode('utf-8'))
    if drain:
        await writer.drain()

def matches(d, *keys):
    return
