from .adrian import Adrian
from .julian import Julian
from .diana import Diana
from .torstein import Torstein
from .trappers import Trappers
from .kalevi import Kalevi
from .leo import Leo

_heros = [Adrian, Julian, Diana, Torstein, Trappers, Kalevi, Leo]
# only one hero working for now, we'll see how we go next...
_heros = [Adrian]

HEROS = {}
HEROS_DESCRIPTION = {}

def update(self, dt):
    """dt is the delta time"""
    for i in range(len(self.till_cooled)):
        self.till_cooled[i] -= dt

    if self.ipt['up']:
        self.rect.top -= self.speed * dt
    elif self.ipt['down']:
        self.rect.top += self.speed * dt
    elif self.ipt['left']:
        self.rect.left -= self.speed * dt
    elif self.ipt['right']:
        self.rect.left += self.speed * dt
    elif self.ipt['space'] and self.till_cooled[self.ipt['ability']] <= 0:
        self.trigger_ability()
        self.till_cooled[self.ipt['ability']] = \
            self.COOLDOWNS[self.ipt['ability']]

for h in HEROS:
    # this is a hack to not have to import a class in every hero's file just
    # to inherit
    h.update = update
    HEROS_DESCRIPTION[h.name] = h.description
    HEROS[h.name] = h
