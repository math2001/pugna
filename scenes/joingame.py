import pygame
import logging
from constants import PORT
from asyncio import open_connection
from utils.gui import TextBox, MessageBox
from utils.network import write, readline

log = logging.getLogger(__name__)

class JoinGame:

    async def on_focus(self, manager):
        self.m = manager
        self.state = 'Waiting for user input'
        self.textbox = TextBox(self.m.uifont)
        self.textbox.focused = True

        self.messagebox = None

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
        log.info("Change state to {!r}".format(newvalue))
        self._state = newvalue

    state = property(lambda self: self._state, setstate)

    async def send_request(self, ip):
        self.state = 'Opening connection'
        try:
            self.m.reader, self.m.writer = await open_connection(ip, PORT)
        except (ConnectionRefusedError, OSError) as e:
            return await self.display_error(e)
        self.state = "Waiting for owner"
        await write(self.m.writer, self.m.uuid, self.m.username)
        response = await readline(self.m.reader)
        if response == 'accepted':
            await self.m.focus("select hero")
        elif response == 'owner already requested':
            await self.confirm_request_again()
        elif response == 'declined':
            await self.request_declined()
        else:
            raise ValueError(f"Unexpected response from server {response!r}")

    async def request_declined(self):
        self.messagebox = MessageBox.new(self.m.uifont,
                                         "Your request was declined\nYou may try again", "OK")
        self.messagebox.rect.center = self.m.rect.center
        self.messagebox.calibre()
        self.state = 'Waiting for user input'

    async def confirm_request_again(self):
        raise NotImplementedError("Display confirm popup")

    async def display_error(self, error):
        self.messagebox = MessageBox.new(self.m.uifont,
                                         "An error has occurred while oppening "
                                         "the connection\n"
                                         f"{error.strerror}", "OK")
        self.messagebox.rect.center = self.m.rect.center
        self.messagebox.calibre()
        self.state = "Waiting for user input"

    async def event(self, e):
        if self.textbox.event(e):
            await self.send_request(self.textbox.text)
        if self.messagebox:
            if self.messagebox.event(e):
                self.messagebox = None

    async def render(self):
        self.m.screen.blit(self.title, self.titlerect)
        self.m.screen.blit(self.label, self.labelrect)

        s, r = self.textbox.render()
        r.midtop = self.labelrect.midbottom
        r.top += 10
        self.m.screen.blit(s, r)

        self.m.uifont.origin = True
        r = self.m.uifont.get_rect(self.state)
        r.midbottom = self.m.rect.centerx, self.m.rect.bottom - 10
        self.m.uifont.render_to(self.m.screen, r, None)

        self.m.suspensiondots(self.m.screen, r, self.m.uifont)

        if self.messagebox:
            self.messagebox.render(self.m.screen)
