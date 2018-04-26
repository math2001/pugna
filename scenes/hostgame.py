import pygame
from socket import gethostbyname, gethostname

import server

class HostGame:

    def on_focus(self, manager):
        self.m = manager
        self.localip = gethostbyname(gethostname())

    def render(self):
        pass
