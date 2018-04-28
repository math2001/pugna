from json import JSONDecoder

async def readline(reader):
    return (await reader.readline()).decode('utf-8').strip()


async def write(writer, *lines, drain=True):
    writer.write(('\n'.join(lines) + '\n').encode('utf-8'))
    if drain:
        await writer.drain()

dec = JSONDecoder().decode
