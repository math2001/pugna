"""
A hard coded cli client to quickly test the gui
"""

import asyncio
import sys

USERNAME = 'client cli'
UUID = 'uuid(client cli)'

async def nr():
    print(f"Sending new request as '{USERNAME}' with '{UUID}'")
    r, w = await asyncio.open_connection('localhost', 9877)
    json = '{"kind": "new request", "by": "' + USERNAME + '", "uuid": "' \
            + UUID + '"}\n'
    w.write(json.encode('utf-8'))
    await w.drain()
    print((await r.readline()).decode('utf-8'))

async def leave():
    print("Connect and quit")
    r, w = await asyncio.open_connection('localhost', 9877)
    w.close()

loop = asyncio.get_event_loop()
task = None
loop.create_task(locals()[sys.argv[1]]())
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
