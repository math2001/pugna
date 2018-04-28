from json import JSONDecoder

dec = JSONDecoder().decode
end = JSONEncoder().encode

class CommunicationClosed(Exception):

    def __init__(self, msg, client):
        self.msg = msg
        self.client = client

async def read(reader):
    result = (await reader.readline()).decode('utf-8')
    if not result:
        raise CommunicationClosed("The communication has been closed", reader)
    return dec(result)

async def write(writer, msg, drain=True):
    writer.write((enc(msg)).encode('utf-8'))
    if drain:
        await writer.drain()

def matches(d, *keys):
    return
