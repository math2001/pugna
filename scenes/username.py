
class Username:

    def __init__(self, m):
        self.m = m

        self.inputbox = self.m.gui.InputBox(
            label='Pick a deadly username',
            center=self.m.rect.center,
            bordercolor=(15, 15, 15),
            input=self.m.gui.Input(maxlength=16),
            ok=self.m.gui.Button(text='Go', width=100),
            onsend=self.onsend)

    async def on_focus(self):
        self.m.gui.activate(self.inputbox)

    async def on_blur(self, next):
        self.m.gui.deactivate(self.inputbox)

    async def onsend(self, element, e):
        self.m.username = self.inputbox.text
        self.m.dev_username = False
        await self.m.focus('Menu')
