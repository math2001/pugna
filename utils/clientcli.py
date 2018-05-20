"""
A hard coded cli client to quickly test the gui
"""

import asyncio
import sys

USERNAME = 'client cli'
UUID = 'uuid(client cli)'

async def newrequest():
    print(f"Sending new request as '{USERNAME}' with '{UUID}'")
    r, w = await asyncio.open_connection('localhost', 9877)
    json = '{"kind": "new request", "by": "' + USERNAME + '", "uuid": "' \
            + UUID + '"}\n'
    w.write(json.encode('utf-8'))
    await w.drain()
    print((await r.readline()).decode('utf-8'))

loop = asyncio.get_event_loop()
task = None
if sys.argv[1] == 'nr':
    loop.create_task(newrequest())

loop.run_forever()
