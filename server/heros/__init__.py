from .adrian import Adrian
from .julian import Julian
from .diana import Diana
from .torstein import Torstein
from .trappers import Trappers
from .kalevi import Kalevi
from .leo import Leo

_heros = [Adrian, Julian, Diana, Torstein, Trappers, Kalevi, Leo]

HEROS = {}

HEROS_DESCRIPTION = {}
for h in HEROS:
    HEROS_DESCRIPTION[h.name] = h.description
    HEROS[h.name] = h
