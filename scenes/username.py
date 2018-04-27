import pygame
import logging
from utils.gui import TextBox, Button

log = logging.getLogger(__name__)

class Username:

    menubtn = False

    async def on_focus(self, manager):
        self.m = manager
        self.m.uifont.origin = True
        self.textbox = TextBox(manager.uifont)
        self.textbox.rect.center = self.m.rect.center

        self.btn = Button(manager.uifont, "OK", maxlength=16)
        self.btn.rect.midleft = self.textbox.rect.midright
        self.btn.rect.left += 10

        self.lbl, self.lblrect = self.m.uifont.render("Enter your username:")
        self.lblrect.midbottom = self.textbox.rect.midtop
        self.lblrect.top -= 10

    async def event(self, e):
        if self.textbox.event(e) is True:
            # TODO: validate username
            self.m.username = self.textbox.text
            await self.m.focus("Menu")

    async def render(self):
        self.textbox.render(self.m.screen)
        self.m.screen.blit(self.lbl, self.lblrect)
