from json import JSONDecoder

class ClientLeft(Exception):

    def __init__(self, msg, reader):
        self.msg = msg
        self.reader = reader

async def readline(reader):
    result = (await reader.readline()).decode('utf-8')
    if not result:
        raise ClientLeft("A client left", reader)
    return result.strip()


async def write(writer, *lines, drain=True):
    writer.write(('\n'.join(lines) + '\n').encode('utf-8'))
    if drain:
        await writer.drain()

dec = JSONDecoder().decode
