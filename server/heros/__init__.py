from .adrian import Adrian

HEROS = [Adrian]
HEROS_DESCRIPTION = {}
for h in HEROS:
    HEROS_DESCRIPTION[h.name] = h.description
