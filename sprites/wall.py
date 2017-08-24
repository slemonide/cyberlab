from .sprite import Sprite
from sprites import sprite_groups


class Wall(Sprite):
    def __init__(self, game, x, y, img):
        super().__init__(game, x, y, img, sprite_groups.solid)
