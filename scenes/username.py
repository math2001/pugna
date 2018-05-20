
class Username:

    def __init__(self, m):
        self.m = m

        self.inputbox = self.m.gui.Input(label='Pick a cool username',
                                         center=self.m.rect.center)

    async def on_focus(self):
        self.m.gui.activate(self.inputbox)

    async def on_blur(self, next):
        self.m.gui.deactivate(self.inputbox)

    async def onsubmit(self):
        self.m.username = self.inputbox.text
        self.m.dev_username = False
