import pygame
import logging
from socket import gethostbyname, gethostname

import server
import asyncio
from collections import namedtuple
from constants import PORT
from utils.gui import ConfirmBox, MessageBox
from utils.classes import *

log = logging.getLogger(__name__)

class HostGame:

    """This class acts as a client, talking to the server *this*
    class initialized
    """

    async def on_focus(self, manager):
        self.m = manager
        self.localip = gethostbyname(gethostname())

        self.messagebox = None
        self.confirmbox = None
        self.connecting_to_server = None

        self.initrender()

        self.m.server = server.Server(self.m.uuid, self.m.loop)

        self.m.state = "Creating server"
        if await self.start_server() is False:
            # couldn't create the server
            return

        self.m.state = 'Opening connection with server'

        self.connecting_to_server = self.m.loop.create_task(
            self.handler_connect_to_server())

    async def start_server(self):
        error = await self.m.server.start(PORT)
        if error is None:
            return True

        self.messagebox = MessageBox.new(self.m.uifont,
                "Couldn't start the server. Remember, you can only host one "
                f"game at a time.\n\n{error}", "OK", height=250)
        self.messagebox.rect.center = self.m.rect.center
        self.messagebox.calibre()
        return False

    async def handler_connect_to_server(self):
        try:
            await self.connect_to_server()
        except ConnectionClosed as e:
            log.debug("Connection closed")
            if e.reader is not self.m.connection.reader:
                # the other player (not the owner) left the game
                raise NotImplement("Show 'other player left' popup")
                # TODO: shutdown the server, and move back to menu

    async def connect_to_server(self):
        self.m.connection = Connection(*await asyncio.open_connection(
            "127.0.0.1", PORT, loop=self.m.loop))
        self.m.state = "Identifying"

        # send uuid and username to the server so that he knows we are the
        # owner. We then have a connection established and the server can talk
        # to us.
        await self.m.connection.write(kind='identification', uuid=self.m.uuid,
                                      username=self.m.username)

        res = await self.m.connection.read('state',
                                           kind='identification state change')
        if res['state'] != "success":
            # TODO: implement gui
            log.critical(f"Unexpected answer while identifying {res!r}")
            raise NotImplementedError("Need to have a nice GUI for this")
        log.debug("successful logging as owner with the server")

        # self.m.loop.create_task(self.listen_for_request())
        await self.listen_for_request()

    async def on_blur(self, next_scene):
        if next_scene.__class__.__name__ == "Menu":
            await self.m.server.shutdown()

    async def listen_for_request(self):
        self.m.state = 'Waiting for an other player to join'

        req = await self.m.connection.read('uuid', 'username',
                                           kind='new request')
        self.m.state = 'Got request from player'

        self.confirmbox = ConfirmBox.new(self.m.uifont,
                                         f"{req['username']} wants to "
                                         "play with you!", "Accept!", "Na...")
        self.confirmbox.rect.center = self.m.rect.center
        self.confirmbox.calibre()

    async def event(self, e):
        if self.messagebox and self.messagebox.event(e):
            return await self.m.focus("Menu")

        if self.confirmbox:
            result = self.confirmbox.event(e)
            if result is True:
                log.info("Request accepted")
                await self.m.connection.write(kind='request state change',
                                              state='accepted')
                self.confirmbox = None
                self.m.state = "Waiting for server green flag"

                response = await self.m.connection.read('heros_description',
                                                        kind='next scene data')

                await self.m.focus("select hero", response['heros_description'])
            elif result is False:
                await self.m.connection.write(kind='request state change',
                                              state='declined')
                self.confirmbox = None
                self.m.loop.create_task(self.listen_for_request())


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
        r = self.m.uifont.get_rect(self.m.state)
        r.midbottom = self.m.rect.centerx, self.m.rect.bottom - 10
        self.m.uifont.render_to(self.m.screen, r, None)

        self.m.suspensiondots(self.m.screen, r, self.m.uifont)

        if self.confirmbox:
            self.confirmbox.render(self.m.screen)

        if self.messagebox:
            self.messagebox.render(self.m.screen)

