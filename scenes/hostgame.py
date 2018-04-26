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

        self.initrender()

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
        await write(self.writer, self.m.uuid)
        await write(self.writer, self.m.username)

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

        self.listener = self.m.loop.create_task(self.listen_for_request())

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
        l.debug("Start listening for requests")
        uuid = await readline(self.reader)
        l.debug(f"Got uuid {uuid!r} from server.")
        username = await readline(self.reader)
        l.debug(f"Got a player request ({username!r})")
        self.request = Request(uuid, username)
        self.state = 'got request from player'

        self.confirmbox = ConfirmBox(f"{username} wants to play with you!",
                                     "Accept!", "Na...")

    def setstate(self, newvalue):
        l.info("Change state to {!r}".format(newvalue))
        self._state = newvalue

    state = property(lambda self: self._state, setstate)


    def initrender(self):
        # generate text once and store it. In the render, we just blit the images
        # on the screen
        # tr is a reference to self.to_render, so it saves me some typing
        tr = self.to_render = []

        self.m.fancyfont.size = 60
        tr.append(self.m.fancyfont.render("Host a game"))
        tr[-1][1].midtop = self.m.rect.centerx, 50

        tr.append(self.m.uifont.render("Your local IP is:"))
        tr[-1][1].midtop = self.m.rect.centerx, tr[-2][1].bottom + 40

        self.m.uifont.size = 40
        tr.append(self.m.uifont.render(self.localip))
        tr[-1][1].midtop = self.m.rect.centerx, tr[-2][1].bottom + 20

        self.m.reset_fonts()

        self.confirmbox = None

    async def render(self):

        for s, r in self.to_render:
            self.m.screen.blit(s, r)

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

        elif self.confirmbox:
            self.confirmbox.render()

