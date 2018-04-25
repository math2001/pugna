import pygame
from utils.gui import TextBox, Options

class Username:
    def on_focus(self, manager):
        self.textbox = TextBox(manager.uifont)
        self.textbox.focused = True

    def event(self, e):
        self.textbox.event(e)

    def update(self):
        pass

    def render(self, screen, rect):
        textbox, txtrect = self.textbox.render()
        txtrect.center = rect.center
        screen.blit(textbox, txtrect)
