from .sprite import Sprite
from sprites import sprite_groups


class Item(Sprite):
    def __init__(self, game, x, y, img):
        super().__init__(game, x, y, img, sprite_groups.items_on_floor)

        self.pickable = None
