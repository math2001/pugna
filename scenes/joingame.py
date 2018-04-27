import pygame
import logging
from constants import PORT
from asyncio import open_connection
from utils.gui import TextBox
from utils.network import write, readline

l = logging.getLogger(__name__)

class JoinGame:

    async def on_focus(self, manager):
        self.m = manager
        self.state = 'waiting for user input'
        self.textbox = TextBox(self.m.uifont)
        self.textbox.focused = True

        self.m.uifont.origin = True

        self.label, self.labelrect = self.m.uifont.render("Enter the "
                                                          "host's IP:")
        self.m.fancyfont.size = 60

        self.title, self.titlerect = self.m.fancyfont.render("Join a game")
        self.titlerect.midtop = self.m.rect.centerx, 50

        self.label, self.labelrect = \
                self.m.uifont.render("Enter the host's IP and press Enter")

        self.labelrect.midtop = self.titlerect.midbottom
        self.labelrect.top += 70

    def setstate(self, newvalue):
        l.info("Change state to {!r}".format(newvalue))
        self._state = newvalue

    state = property(lambda self: self._state, setstate)

    async def send_request(self, ip):
        try:
            self.m.reader, self.m.writer = await open_connection(ip, PORT)
        except (ConnectionRefusedError, OSError) as e:
            await self.display_error(e)
        await write(self.m.writer, self.m.uuid, self.m.username)
        response = await readline(self.m.reader)
        if response == 'accepted':
            await self.m.focus("select champion")
        elif response == 'owner already requested':
            await self.confirm_request_again()
        elif response == 'declined':
            await self.request_declined()

    async def request_declined(self):
        raise NotImplementedError("Display status message")

    async def confirm_request_again(self):
        raise NotImplementedError("Display confirm popup")

    async def display_error(self, error):
        raise NotImplementedError(error.strerror)

    async def event(self, e):
        if self.textbox.event(e):
            self.state = 'waiting for server reply'
            await self.send_request(self.textbox.text)


    async def render(self):
        self.m.screen.blit(self.title, self.titlerect)
        self.m.screen.blit(self.label, self.labelrect)

        s, r = self.textbox.render()
        r.midtop = self.labelrect.midbottom
        r.top += 10
        self.m.screen.blit(s, r)
