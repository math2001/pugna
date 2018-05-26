from pygame.rect import Rect

class Adrian:

    name = "Adrian"
    description = "A redoutable stone thrower. I wouldn't get in his sight as " \
                  "long as he has a sling in his hand"

    # these are the "permanants" stats of the hero.
    # They have an equivalent lower case attribute, which can be boosted by
    # some ability for example
    MAX_HEALTH = 750
    SPEED = 10
    DAMAGE = 30
    ARMOR = 0
    TRUE_DAMAGE = False
    # in seconds
    COOLDOWNS = [1, 8, 23]

    STONE_SPEED = 15
    STONE_DAMAGE = 43
    STONE_RECT = Rect(0, 0, 7, 7)

    def __init__(self):
        self.health = Adrian.MAX_HEALTH
        self.speed = Adrian.SPEED
        self.damage = Adrian.DAMAGE
        self.armor = Adrian.ARMOR
        self.true_damage = Adrian.TRUE_DAMAGE

        self.till_cooled = [0, 0, 0]

        self.stone_speed = Adrian.STONE_SPEED
        self.stone_damage = Adrian.STONE_DAMAGE

        # the center of hero
        self.rect = Rect(0, 0, 40, 40)
        # The input state will automatically be updated by the server
        self.ipt = None

