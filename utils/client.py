import asyncio
from utls.connection import Connection

__all__ = ['Client']

class Response:

    def __init__(self, **kwargs):
        self.__dict__ = kwargs
        self.error = getattr(self, 'error', False)

class Client:

    """An API to communicate with the server"""

    def __init__(self, host, port):
        self.co = Connection(*asyncio.open_connection(host, port))

    async def login(self, username, uuid):
        await self.co.write(kind='identification', by=username, uuid=uuid)
        res = await self.co.read()
        if res['kind'] != 'identification state change':
            return Response(error=True,
                            msg=f"Invalid request kind: {res['kind']!r}")
        if res['state'] == 'accepted':
            return Response(msg=f"Accepted!")
        elif res['state'] == 'accepted':
            return

    def shutdown(self):
        self.co.close()
