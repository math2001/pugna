import pygame
import logging
from utils.gui import TextBox, Options

l = logging.getLogger(__name__)

class Username:

    def on_focus(self, manager):
        self.m = manager
        self.textbox = TextBox(manager.uifont)
        self.textbox.focused = True

        self.m.uifont.origin = True

    def event(self, e):
        if self.textbox.event(e) is True:
            # TODO: validate username
            self.m.username = self.textbox.text
            self.m.focus("Menu")

    def render(self):
        textbox, txtrect = self.textbox.render()
        txtrect.center = self.m.rect.center

        s, r = self.m.uifont.render("Enter your username and press enter")
        r.midbottom = txtrect.midtop
        r.bottom -= 10
        self.m.screen.blit(s, r)
        self.m.screen.blit(textbox, txtrect)

    def on_blur(self):
        self.m.uifont.origin = False
