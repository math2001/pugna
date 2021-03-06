import pygame
import logging
from asyncio import open_connection
from constants import PORT
from utils.gui import TextBox, MessageBox, Button
from utils.classes import *

log = logging.getLogger(__name__)

class JoinGame:

    async def on_focus(self, manager):
        self.m = manager
        self.m.state = 'Waiting for user input'

        self.messagebox = None

        self.m.uifont.origin = True

        self.label, self.labelrect = self.m.uifont.render("Enter the "
                                                          "host's IP:")
        self.m.fancyfont.size = 60

        self.title, self.titlerect = self.m.fancyfont.render("Join a game")
        self.titlerect.midtop = self.m.rect.centerx, 50

        self.label, self.labelrect = \
                self.m.uifont.render("Enter the host's IP")

        self.labelrect.midtop = self.titlerect.midbottom
        self.labelrect.top += 70

        # default for dev
        self.textbox = TextBox(self.m.uifont, initialtext="127.0.0.1")
        self.textbox.rect.midtop = (self.labelrect.centerx,
                                    self.labelrect.bottom + 10)
        self.submitbtn = Button(self.m.uifont, "Send request")
        self.submitbtn.rect.midleft = self.textbox.rect.midright
        self.submitbtn.rect.left += 10

    async def send_request(self, ip):
        self.m.state = 'Opening connection'
        try:
            self.m.connection = Connection(*(await open_connection(ip, PORT,
                                                            loop=self.m.loop)))
        except (ConnectionRefusedError, OSError) as e:
            return await self.display_error(e)
        await self.m.connection.write(uuid=self.m.uuid,
                                      username=self.m.username,
                                      kind='identification')

        self.m.state = "Waiting for owner's reply"
        self.submitbtn.enabled = False

        error = None
        try:
            res = await self.m.connection.read('state', 'reason',
                                               kind='request state change')
        except ConnectionClosed as e:
            error = e

        if error is not None:
            log.error(f"Connection closed: {error!r}")
            self.messagebox = MessageBox.new(self.m.uifont,
                                             "The connection with the server "
                                             "seems to have been closed.\n"
                                             "The owner probably just left",
                                             'How rude!')
        elif res['state'] == 'accepted':
            data = await self.m.connection.read('heros_description',
                                                kind='next scene data')
            return await self.m.focus("select hero", data['heros_description'])
        elif res['reason'] == 'enough players for now':
            log.info("Request declined by server (enough player)")
            self.messagebox = MessageBox.new(self.m.uifont,
                                             "Another player has already "
                                             'joined this game...\n', 'Crap')
        elif res['reason'] == 'owner declined':
            log.info("Request declined by owner (lol)")
            self.messagebox = MessageBox.new(self.m.uifont,
                                             "Your request was declined.\n"
                                             "You may try again", 'Really?!')
        else:
            log.critical(f"Unexpected response from server {res!r}")
            self.messagebox = MessageBox.new(self.m.uifont,
                "Recieved an unexpected response from the server (see log).\n"
                "Please try again.",
                "Hum... Ok")

        self.submitbtn.enabled = True
        self.messagebox.rect.center = self.m.rect.center
        self.messagebox.calibre()
        self.m.state = 'Waiting for user input'

    async def display_error(self, error):
        log.error(f"Error occured while connecting: {error}")
        self.messagebox = MessageBox.new(self.m.uifont,
            "An error has occurred while oppening the connection\n"
            f"{error.strerror}", 'Oh no!', height=200)
        self.messagebox.rect.center = self.m.rect.center
        self.messagebox.calibre()
        self.m.state = "Waiting for user input"

    async def event(self, e):
        if self.messagebox:
            if self.messagebox.event(e):
                self.messagebox = None
            return # prevent input is message box present
        if self.textbox.event(e) or self.submitbtn.event(e):
            self.m.loop.create_task(self.send_request(self.textbox.text))

    async def render(self):
        self.m.screen.blit(self.title, self.titlerect)
        self.m.screen.blit(self.label, self.labelrect)

        self.textbox.render(self.m.screen)
        self.submitbtn.render(self.m.screen)

        self.m.uifont.origin = True
        r = self.m.uifont.get_rect(self.m.state)
        r.midbottom = self.m.rect.centerx, self.m.rect.bottom - 10
        self.m.uifont.render_to(self.m.screen, r, None)

        self.m.suspensiondots(self.m.screen, r, self.m.uifont)

        if self.messagebox:
            self.messagebox.render(self.m.screen)
