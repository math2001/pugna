from pygame.rect import Rect
from json import JSONDecoder

dec = JSONDecoder().decode

class Map:

    """The map will manage the collisions of players and
    projectiles with the map's structure.
    """

    def __init__(self):
        self.width, self.height, self.obstacles, self.start1, self.start2 = \
            self.load_map()

    def load_map(self):
        with open('./map.json', 'r', encoding='utf-8') as fp:
            map = dec(fp.read())

        return (map['width'], map['height'], map['obstacles'], map['start1'],
                map['start2'])
