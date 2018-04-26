import pygame
import logging
from socket import gethostbyname, gethostname

import server
import asyncio
from collections import namedtuple
from constants import PORT
from utils.network import *
from utils.gui import ConfirmBox

l = logging.getLogger(__name__)

Request = namedtuple("Request", 'uuid username')

class HostGame:

    """This class acts as a client, talking to the server *this*
    class initialized
    """

    async def on_focus(self, manager):
        self.m = manager
        self.localip = gethostbyname(gethostname())

        self.animdots = 0

        self.server = server.Server(self.m.uuid, self.m.username)

        self.state = "creating server"

        # self.connection = self.m.loop.create_task(self.server.start(PORT))
        self.connection = await self.server.start(PORT)

        self.state = 'opening connection'

        self.m.loop.create_task(self.connect_to_server())

    async def connect_to_server(self):
        l.debug("Open connection with server")
        self.reader, self.writer = await asyncio.open_connection("127.0.0.1", PORT, loop=self.m.loop)
        self.state = "identifying"

        l.debug("Send ids to the server")

        # send uuid and username to the server so that he knows we are the
        # owner. We then have a connection established and server can talk to
        # us.
        await write(self.writer, self.m.uuid + '\n')
        await write(self.writer, self.m.username + '\n')

        answer = await readline(self.reader)
        if answer != "successful identification":
            # can't be bothered to do that right now since it is very unlikely
            # to happen
            l.critical("Unexpected answer while "
                       "identifying {!r}".format(answer))
            raise NotImplementedError("Need to have a nice GUI for this")
        l.debug("successful logging as owner with the server")

        self.state = 'waiting for other player'
        self.request = None

        # self.listener = self.m.loop.create_task(self.listen_for_request())

    async def on_blur(self):
        l.debug("Stop listening for requests")
        await self.server.close()
        # self.connection.cancel()
        # self.writer.transport.abort()
        # self.writer.close()
        # self.listener.cancel()
        # self.writer.write_eof()
        # await self.writer.drain()

    async def listen_for_request(self):
        l.debug("Awating for request...")
        uuid = await readline(self.reader)
        username = await reader(self.reader)
        self.state = 'got request from player'
        self.request = Request(uuid, username)

    def setstate(self, newvalue):
        l.info("Change state to {!r}".format(newvalue))
        self._state = newvalue

    state = property(lambda self: self._state, setstate)


    async def render(self):
        top = 50
        size = 60
        r = self.m.fancyfont.get_rect("Host a game", size=size)
        r.midtop = self.m.rect.centerx, top
        self.m.fancyfont.render_to(self.m.screen, r, None, size=size)

        top = r.bottom + 40

        r = self.m.uifont.get_rect("Your local IP is:")
        r.centerx, r.top = self.m.rect.centerx, top
        self.m.uifont.render_to(self.m.screen, r, None)

        top = r.bottom + 20

        size = 40
        r = self.m.uifont.get_rect(self.localip, size=size)
        r.centerx, r.top = self.m.rect.centerx, top
        self.m.uifont.render_to(self.m.screen, r, None, size=size)

        top = r.bottom + 130

        if self.m.frames_count % 20 == 0:
            self.animdots += 1
            if self.animdots == 4:
                self.animdots = 0

        if self.state == 'waiting for other player':
            self.m.uifont.origin = True
            r = self.m.uifont.get_rect("Waiting for an other player to join")
            r.midbottom = self.m.rect.centerx, self.m.rect.bottom - 10
            self.m.uifont.render_to(self.m.screen, r, None)

            dr = self.m.uifont.get_rect('.' * self.animdots)
            dr.topleft = r.topright
            self.m.uifont.render_to(self.m.screen, dr, None)

        elif self.state == 'got request from player':
            ConfirmBox("{0} wants to play with you." \
                        .format(self.request.username))
