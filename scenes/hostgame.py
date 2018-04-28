import pygame
import logging
from socket import gethostbyname, gethostname

import server
import asyncio
from collections import namedtuple
from constants import PORT
from utils.network import *
from utils.gui import ConfirmBox

log = logging.getLogger(__name__)

Request = namedtuple("Request", 'uuid username')

class HostGame:

    """This class acts as a client, talking to the server *this*
    class initialized
    """

    async def on_focus(self, manager):
        self.m = manager
        self.localip = gethostbyname(gethostname())

        self.initrender()

        self.server = server.Server(self.m.uuid, self.m.username, self.m.loop)

        self.state = "Creating server"

        await self.server.start(PORT)

        self.state = 'Opening connection with server'

        self.m.loop.create_task(self.connect_to_server())

    async def connect_to_server(self):
        self.m.reader, self.m.writer = await asyncio.open_connection(
            "127.0.0.1", PORT, loop=self.m.loop)
        self.state = "Identifying"

        log.debug("Send ids to the server")

        # send uuid and username to the server so that he knows we are the
        # owner. We then have a connection established and server can talk to
        # us.
        await write(self.m.writer, self.m.uuid)
        await write(self.m.writer, self.m.username)

        answer = await readline(self.m.reader)
        if answer != "successful identification":
            # can't be bothered to do that right now since it is very unlikely
            # to happen
            log.critical("Unexpected answer while "
                       "identifying {!r}".format(answer))
            raise NotImplementedError("Need to have a nice GUI for this")
        log.debug("successful logging as owner with the server")

        self.listener = self.m.loop.create_task(self.listen_for_request())

    async def on_blur(self):
        log.debug("Stop listening for requests")
        await self.server.close()
        # self.connection.cancel()
        # self.m.writer.transport.abort()
        # self.m.writer.close()
        # self.listener.cancel()
        # self.m.writer.write_eof()
        # await self.m.writer.drain()

    async def listen_for_request(self):
        self.request = None
        self.confirmbox = None
        self.state = 'Waiting for an other player to join'

        log.debug("Start listening for requests")
        uuid = await readline(self.m.reader)
        log.debug(f"Got uuid {uuid!r} from server.")
        username = await readline(self.m.reader)
        log.debug(f"Got a player request ({username!r})")
        self.request = Request(uuid, username)
        self.state = 'Got request from player'

        self.confirmbox = ConfirmBox.new(self.m.uifont,
                                         f"{username} wants to play with you!",
                                        "Accept!", "Na...")
        self.confirmbox.rect.center = self.m.rect.center
        self.confirmbox.calibre()

    async def event(self, e):
        if self.confirmbox:
            result = self.confirmbox.event(e)
            if result is True:
                log.info("Request accecepted")
                await write(self.m.writer, 'accepted')
                self.confirmbox = None
                self.state = "Waiting for server green flag"
                response = await readline(self.m.reader)
                log.debug(f"Got response from server {response!r}")
                if response == 'select hero':
                    await self.m.focus("select hero")
                else:
                    log.critical(f"Got unexpected response {response!r}")
                    raise NotImplementedError("This shouldn't happen")
            elif result is False:
                await write(self.m.writer, 'declined')
                self.listener = self.m.loop.create_task(
                                self.listen_for_request())


    def initrender(self):
        # generate text once and store it. In the render, we just blit the
        # images on the screen tr is a reference to self.to_render, so it saves
        # me some typing
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

        self.m.uifont.origin = True
        r = self.m.uifont.get_rect(self.state)
        r.midbottom = self.m.rect.centerx, self.m.rect.bottom - 10
        self.m.uifont.render_to(self.m.screen, r, None)

        self.m.suspensiondots(self.m.screen, r, self.m.uifont)

        if self.confirmbox:
            self.confirmbox.render(self.m.screen)

    def setstate(self, newvalue):
        log.info("Change state to {!r}".format(newvalue))
        self._state = newvalue

    state = property(lambda self: self._state, setstate)


