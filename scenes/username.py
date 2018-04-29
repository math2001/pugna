import pygame
import logging
import string
from utils.gui import TextBox, Button, origin

log = logging.getLogger(__name__)

class Username:

    menubtn = False
    allowed_username_characters = string.ascii_letters + string.digits + ' ' \
        + string.punctuation

    async def on_focus(self, manager):
        self.m = manager
        self.m.uifont.origin = True
        self.textbox = TextBox(manager.uifont)
        self.textbox.rect.center = self.m.rect.center

        self.btn = Button(manager.uifont, "OK", maxlength=16,
                          height=self.textbox.rect.height)
        self.btn.rect.midleft = self.textbox.rect.midright
        self.btn.rect.left += 10

        self.lbl, self.lblrect = self.m.uifont.render("Enter your username:")
        self.lblrect.midbottom = self.textbox.rect.midtop
        self.lblrect.top -= 10

        self.error = None

    def validate_username(self):
        u = self.textbox.text
        self.error = None
        if len(u) < 4:
            self.error = "Come on... Give yourself a long name!"
            return

        for char in u:
            if char not in Username.allowed_username_characters:
                self.error = f"{char!r} not allowed mate... Sorry."
                return
        return True

    async def event(self, e):
        if (self.textbox.event(e) or self.btn.event(e)) \
                and self.validate_username():
            self.m.username = self.textbox.text
            log.info(f"Logged as {self.m.username!r}")
            await self.m.focus("Menu")

    async def render(self):
        self.textbox.render(self.m.screen)
        self.m.screen.blit(self.lbl, self.lblrect)
        self.btn.render(self.m.screen)
        if self.error:
            with origin(self.m.uifont, False):
                r = self.m.uifont.get_rect(self.error)
                r.midtop = self.m.rect.centerx, self.btn.rect.bottom + 10
                self.m.uifont.render_to(self.m.screen, r, None,
                                        fgcolor=pygame.Color('tomato'),
                                        style=2) # italic
