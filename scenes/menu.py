import pygame

class Menu:

    def __init__(self, m):
        self.m = m

        top = 150

        self.btns = []
        for txt in ['host game', 'join game', 'about', 'quit']:
            btn = self.m.gui.Button(text=txt, onsend=self.btnclick,
                                    onmouseenter=self.btnmouseenter,
                                    onmouseleave=self.btnmouseleave,
                                    font='fancy', paddingy=40, width=300,
                                    size=35,
                                    centerx=self.m.rect.centerx, top=top)
            top = btn.rect.bottom + 20
            self.btns.append(btn)

    async def btnclick(self, btn, e):
        if btn.opt.text == 'quit':
            return await self.m.quit()
        await self.m.focus(btn.opt.text.title().replace(' ', ''))

    async def btnmouseenter(self, btn, e):
        btn.setopt(bordercolor=pygame.Color("Tomato"))

    async def btnmouseleave(self, btn, e):
        btn.setopt(bordercolor=pygame.Color(30, 30, 30))

    async def on_focus(self):
        for btn in self.btns:
            self.m.gui.activate(btn)

    async def on_blur(self, scene):
        for btn in self.btns:
            self.m.gui.deactivate(btn)
