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
    # the size of the personage
    RADIUS = 7

    def __init__(self):
        self.health = Adrian.MAX_HEALTH
        self.speed = Adrian.SPEED
        self.damage = Adrian.DAMAGE
        self.armor = Adrian.ARMOR
        self.true_damage = Adrian.TRUE_DAMAGE
        self.raduis = Adrian.radius

        # the center of hero
        self.position = None
