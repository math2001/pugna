import pygame
import logging
from socket import gethostbyname, gethostname

import server
import asyncio
from constants import PORT
from utils.network import *

l = logging.getLogger(__name__)

class HostGame:

    """This class acts as a client, talking to the server *this*
    class initialized
    """

    def on_focus(self, manager):
        self.m = manager
        self.localip = gethostbyname(gethostname())

        self.state = "opening connection"

        self.server = server.Server(self.m.uuid, self.m.username, PORT)
        self.loop = asyncio.get_event_loop()

        self.reader, self.writer = self.loop.run_until_complete(
            asyncio.open_connection("127.0.0.1", PORT, loop=self.loop))

        self.state = "identifying"

        # send uuid and username to the server so that he knows we are the
        # owner. We then have a connection established and server can talk to
        # us.
        self.loop.run_until_complete(write(self.writer, self.m.uuid + '\n'))
        self.loop.run_until_complete(write(self.writer,
                                           self.m.username + '\n'))

        answer = self.loop.run_until_complete(readline(self.reader))
        if answer != "successful identification":
            # can't be bothered to do that right now since it is very unlikely
            # to happen
            l.critical("Unexpected answer while "
                       "identifying {!r}".format(answer))
            raise NotImplementedError("Need to have a nice GUI for this")

        self.state = 'waiting for other player'

        self.animdots = 0

    def setstate(self, newvalue):
        l.info("Change state to {!r}".format(newvalue))
        self._state = newvalue

    state = property(lambda self: self._state, setstate)

    def render(self):
        top = 50
        size = 60
        r = self.m.fancyfont.get_rect("Hosting a game...", size=size)
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
            r.midtop = self.m.rect.centerx, top
            self.m.uifont.render_to(self.m.screen, r, None)

            dr = self.m.uifont.get_rect('.' * self.animdots)
            dr.topleft = r.topright
            self.m.uifont.render_to(self.m.screen, dr, None)

