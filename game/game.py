import math
import sys
from os import path, getcwd
from sprites import sprite_groups

from game.map import *
from items.pickable import Pickable
from nanogui import Nanogui
from sprites.door import Door
from sprites.item import Item
from sprites.player import Player
from sprites.wall import Wall
from triggers import *
from ui.camera import *
from ui.fov import calc_fov
from ui.spritesheet import Spritesheet


class Game:
    def __init__(self, display):

        # Contains pictures displayed on the player's screen
        self.picture_queue = [] # TODO: finish

        # Contains text displayed on the player's screen
        self.text_queue = []

        # Contains menus displayed on the player's screen
        self.menu_queue = [] # TODO: finish

        # Contains action triggers
        self.triggers = []

        # Contains the user-controlled player
        self.player = None

        # Contains keyboard keys just pressed
        # TODO: @Kuroneko: when does this gets updated?
        self.keys_just_pressed = {}

        # Contains joystick controls just pressed
        # TODO: @Kuroneko: when does this gets updated?
        self.joystick_just_pressed = {}

        # Contains the spritesheet. Useful for defining sprites
        self.spritesheet = None

        # Updates user's FOV
        self.update_fov = True

        self.__display__ = display
        self.__clock__ = pg.time.Clock()
        pg.display.set_caption(WINDOW_TITLE)

        joysticks = [pg.joystick.Joystick(x) for x in range(pg.joystick.get_count())]
        self.__joystick__ = None
        if len(joysticks) > 0:
            self.__joystick__ = joysticks[0]
            self.__joystick__.init()

        self.__map__ = None
        self.__camera__ = None
        self.__playing__ = False
        self.__dt__ = 0.0

        self.__textBox__ = pg.image.load("assets/textBox.png").convert_alpha()
        self.__font__ = pg.font.Font("assets/fonts/Arcon.otf", 20)
        self.__fontSpace__ = pg.font.Font("assets/fonts/Arcon.otf", 14)

        self.__gui__ = Nanogui()
        self.__visibility_data__ = None  # [x][y] -> True, False
        self.__fov_data__ = None  # [x][y] -> True, False

    def load(self, map_name):
        """
        Loads new map with the given name
        :param map_name: map to be loaded
        :return: nothing
        """
        assets_folder = path.join(getcwd(), 'assets')
        self.__map__ = Map(path.join(assets_folder, 'maps/' + map_name + '.json'))

        self.spritesheet = Spritesheet(path.join(assets_folder, 'spritesheet.png'), 32)
        wall_img = self.spritesheet.get_image_at_row_col(0, 0)
        apple_img = self.spritesheet.get_image_alpha_at_row_col(1, 0)

        self.__visibility_data__ = [[True] * self.__map__.height for i in range(self.__map__.width)]
        self.__fov_data__ = [[True] * self.__map__.height for i in range(self.__map__.width)]

        for node in self.__map__.objects:
            x, y = node['x'], node['y']
            if node["name"] == 'WALL':
                Wall(self, x, y, wall_img)
                self.__visibility_data__[x][y] = False
            elif node["name"] == 'PLAYER':
                self.player = Player(self, x, y)
            elif node["name"] == 'APPLE':
                item = Item(self, x, y, apple_img)
                item.pickable = Pickable(item, 'apple', False, 1, False)
            elif node["name"] == "DOOR":
                Door(self, x, y, node["dir"])
                self.__visibility_data__[x][y] = False  # TODO opened doors visibility

        for trigger in self.__map__.triggers:
            TextTrigger(self,
                        pg.Rect(trigger["x"], trigger["y"], trigger["width"], trigger["height"]),
                        trigger["text"])

        self.__camera__ = Camera(self.__map__.width_screen, self.__map__.height_screen)

    def __update__(self):
        self.__gui__.pre(self.__joystick__)

        for sprite in sprite_groups.all_sprites:
            sprite.update(self.__dt__)

        if self.__camera__.update(self.player) or self.update_fov:
            player_hit_rect = self.player.get_hit_rect()
            player_tilex = math.floor(player_hit_rect.x / TILE_SIZE)
            player_tiley = math.floor(player_hit_rect.y / TILE_SIZE)

            self.__fov_data__ = calc_fov(player_tilex, player_tiley, FOV_RADIUS,
                                         self.__visibility_data__, self.__fov_data__)
            self.update_fov = False

        self.__gui__.after()

    def __draw__(self):
        self.__display__.fill(BG_COLOR)

        # TODO layering
        for sprite in sprite_groups.all_sprites:
            if sprite != self.player and not isinstance(sprite, Item):
                self.__display__.blit(sprite.image, self.__camera__.transform(sprite))

        for sprite in sprite_groups.items_on_floor:
            tilex = math.floor(sprite.x)
            tiley = math.floor(sprite.y)
            if self.__fov_data__[tilex][tiley]:
                self.__display__.blit(sprite.image, self.__camera__.transform(sprite))

        if DEBUG_FOV:
            self.__draw_fov__()

        self.__display__.blit(self.player.image, self.__camera__.transform(self.player))
        if self.text_queue:
            self.__put_text_on_screen__(self.text_queue[-1])

        self.__gui__.draw()
        pg.display.flip()

    def run(self):
        """
        Run the game
        :return: nothing
        """
        self.__playing__ = True
        while self.__playing__:
            self.__dt__ = self.__clock__.tick(FPS) / 1000
            self.__events__()
            self.__update__()
            self.__draw__()

    def __quit__(self):
        pg.quit()
        sys.exit()

    def __events__(self):
        self.keys_just_pressed.clear()
        self.joystick_just_pressed.clear()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.__quit__()
            if event.type == pg.KEYDOWN:
                self.keys_just_pressed[event.key] = True
                if event.key == pg.K_ESCAPE:
                    self.__quit__()
                if event.key == pg.K_F11:
                    self.__toggle_fullscreen__()
            if event.type == pg.JOYBUTTONDOWN:
                self.joystick_just_pressed[event.button] = True

    def __toggle_fullscreen__(self):
        """Taken from http://pygame.org/wiki/__toggle_fullscreen__"""

        screen = pg.display.get_surface()
        tmp = screen.convert()
        caption = pg.display.get_caption()
        cursor = pg.mouse.get_cursor()

        w, h = screen.get_width(), screen.get_height()
        flags = screen.get_flags()
        bits = screen.get_bitsize()

        pg.display.quit()
        pg.display.init()

        self.__display__ = pg.display.set_mode((w, h), flags ^ pg.FULLSCREEN, bits)
        self.__display__.blit(tmp, (0, 0))
        pg.display.set_caption(*caption)

        pg.key.set_mods(0)

        pg.mouse.set_cursor(*cursor)

        return screen

    # TODO: remove as game.get_key_jp can do the same thing
    def get_key_jp(self, key):
        # get key just pressed (clears on new frame)
        if key in self.keys_just_pressed:
            return True
        return False

    # TODO: remove as game.joystick_just_pressed can do the same thing
    def get_joystick_jp(self, button):
        # get joystick button just pressed (clears on new frame)
        if button in self.joystick_just_pressed:
            return True
        return False

    # TODO: remove and make game.__joystick__ public
    def get_axis(self, number):
        if self.__joystick__ is not None:
            return self.__joystick__.get_axis(number)
        return 0.0

    def __put_text_on_screen__(self, text):
        self.__display__.blit(self.__textBox__, (0, 360))
        self.__display__.blit(self.__font__.render(text, True, (255, 255, 255)), (150, 390))
        self.__display__.blit(self.__fontSpace__.render("[SPACE]", True, (255, 255, 255)), (560, 440))
        pg.display.flip()

    # TODO: this is a sprite's property, so move this to Sprite class
    def set_visibility(self, tilex, tiley, value):
        self.__visibility_data__[tilex][tiley] = value
        self.update_fov = True

    def __draw_fov__(self):
        for x in range(len(self.__fov_data__)):
            for y in range(len(self.__fov_data__[0])):
                if self.__fov_data__[x][y]:
                    newx, newy = self.__camera__.transform_xy(x * TILE_SIZE, y * TILE_SIZE)
                    pg.draw.rect(self.__display__, (200, 200, 200), pg.Rect(newx, newy,
                                                                            TILE_SIZE, TILE_SIZE), 1)