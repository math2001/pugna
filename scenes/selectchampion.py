import pygame


class SelectChampion:

    async def on_focus(self, manager):
        self.m = manager

    async def render(self):
        rect = self.m.fancyfont.get_rect("Champion selection...")
        rect.center = self.m.rect.center
        self.m.fancyfont.render_to(self.m.screen, rect, None)
