import asyncio
import logging
from utils.connection import Connection

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

__all__ = ['Client']

def handle_exception(fn):
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except Exception as e:
            log.exception("Exception occurred on client's API")
            return Response(
                error=True,
                exception=e,
                msg=f'An exception of type {e.__class__.__name__!r} has '
                    'occurred. Please see the logs for details and report it.'
                    '\n\nSorry about that :(')
    return wrapper

class Response:

    def __init__(self, **kwargs):
        self.__dict__ = kwargs
        self.error = getattr(self, 'error', False)

class Client:

    """An API to communicate with the server"""

    @classmethod
    async def new(cls, host, port):
        self = cls()
        self.co = Connection(*await asyncio.open_connection(host, port))
        return self

    @handle_exception
    async def login(self, username, uuid):
        """Logs in the server as the ONWER"""
        log.debug("Log into the server")
        await self.co.write(kind='identification', by=username, uuid=uuid)
        log.debug("Reading from the server")
        res = await self.co.read()
        if res['kind'] != 'identification state change':
            log.critical(f"Invalid request kind: got {res['kind']!r} instead of"
                         "'identification state change'")
            return Response(error=True, accepted=None,
                            msg=f"Invalid request kind: {res['kind']!r}")
        if res['state'] == 'accepted':
            return Response(accepted=True)
        elif res['state'] == 'refused':
            return Response(accepted=False, msg=res['reason'])

    @handle_exception
    async def findplayer(self):
        res = await self.co.read()
        if res['kind'] != 'new request':
            log.critical(f"Invalid request kind: got {res['kind']!r} instead of"
                         "'new request'")
            return Response(error=True,
                            msg=f"Invalid request kind: {res['kind']!r}")
        return Response(by=res['by'])

    def shutdown(self):
        """Because this is based on Connection.close(), the same problem
        occurs (we can only order to close the connection, but we can check)"""
        self.co.close()
