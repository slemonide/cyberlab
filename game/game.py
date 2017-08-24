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

        self.__display__ = display
        self.__clock__ = pg.time.Clock()
        pg.display.set_caption(WINDOW_TITLE)

        joysticks = [pg.joystick.Joystick(x) for x in range(pg.joystick.get_count())]
        self.__joystick__ = None
        if len(joysticks) > 0:
            self.__joystick__ = joysticks[0]
            self.__joystick__.init()

        self.triggers = []
        self.spritesheet = None
        self.map = None
        self.player = None
        self.camera = None
        self.playing = False
        self.dt = 0.0
        self.keys_just_pressed = {}
        self.joystick_just_pressed = {}

        self.textBox = pg.image.load("assets/textBox.png").convert_alpha()
        self.font = pg.font.Font("assets/fonts/Arcon.otf", 20)
        self.fontSpace = pg.font.Font("assets/fonts/Arcon.otf", 14)

        self.gui = Nanogui()
        self.visibility_data = None  # [x][y] -> True, False
        self.fov_data = None  # [x][y] -> True, False
        self.update_fov = True

    def load(self):
        assets_folder = path.join(getcwd(), 'assets')
        self.map = Map(path.join(assets_folder, 'maps/map1.json'))

        self.spritesheet = Spritesheet(path.join(assets_folder, 'spritesheet.png'), 32)
        wall_img = self.spritesheet.get_image_at_row_col(0, 0)
        apple_img = self.spritesheet.get_image_alpha_at_row_col(1, 0)

        self.visibility_data = [[True] * self.map.height for i in range(self.map.width)]
        self.fov_data = [[True] * self.map.height for i in range(self.map.width)]

        for node in self.map.objects:
            x, y = node['x'], node['y']
            if node["name"] == 'WALL':
                Wall(self, x, y, wall_img)
                self.visibility_data[x][y] = False
            elif node["name"] == 'PLAYER':
                self.player = Player(self, x, y)
            elif node["name"] == 'APPLE':
                item = Item(self, x, y, apple_img)
                item.pickable = Pickable(item, 'apple', False, 1, False)
            elif node["name"] == "DOOR":
                Door(self, x, y, node["dir"])
                self.visibility_data[x][y] = False  # TODO opened doors visibility

        for trigger in self.map.triggers:
            TextTrigger(self,
                        pg.Rect(trigger["x"], trigger["y"], trigger["width"], trigger["height"]),
                        trigger["text"])

        self.camera = Camera(self.map.width_screen, self.map.height_screen)

    def update(self):
        self.gui.pre(self.__joystick__)

        for sprite in sprite_groups.all_sprites:
            sprite.update(self.dt)

        if self.camera.update(self.player) or self.update_fov:
            player_hit_rect = self.player.get_hit_rect()
            player_tilex = math.floor(player_hit_rect.x / TILE_SIZE)
            player_tiley = math.floor(player_hit_rect.y / TILE_SIZE)

            self.fov_data = calc_fov(player_tilex, player_tiley, FOV_RADIUS,
                                     self.visibility_data, self.fov_data)
            self.update_fov = False

        self.gui.after()

    def draw(self):
        self.__display__.fill(BG_COLOR)

        # TODO layering
        for sprite in sprite_groups.all_sprites:
            if sprite != self.player and not isinstance(sprite, Item):
                self.__display__.blit(sprite.image, self.camera.transform(sprite))

        for sprite in sprite_groups.items_on_floor:
            tilex = math.floor(sprite.x)
            tiley = math.floor(sprite.y)
            if self.fov_data[tilex][tiley]:
                self.__display__.blit(sprite.image, self.camera.transform(sprite))

        if DEBUG_FOV:
            self.draw_fov()

        self.__display__.blit(self.player.image, self.camera.transform(self.player))
        if self.text_queue:
            self.bot_message(self.text_queue[-1])

        self.gui.draw()
        pg.display.flip()

    def run(self):
        self.playing = True
        while self.playing:
            self.dt = self.__clock__.tick(FPS) / 1000
            self.events()
            self.update()
            self.draw()

    def quit(self):
        pg.quit()
        sys.exit()

    def events(self):
        self.keys_just_pressed.clear()
        self.joystick_just_pressed.clear()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()
            if event.type == pg.KEYDOWN:
                self.keys_just_pressed[event.key] = True
                if event.key == pg.K_ESCAPE:
                    self.quit()
                if event.key == pg.K_F11:
                    self.toggle_fullscreen()
            if event.type == pg.JOYBUTTONDOWN:
                self.joystick_just_pressed[event.button] = True

    def toggle_fullscreen(self):
        """Taken from http://pygame.org/wiki/toggle_fullscreen"""

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

    def get_key_jp(self, key):
        # get key just pressed (clears on new frame)
        if key in self.keys_just_pressed:
            return True
        return False

    def get_joystick_jp(self, button):
        # get joystick button just pressed (clears on new frame)
        if button in self.joystick_just_pressed:
            return True
        return False

    def get_axis(self, number):
        if self.__joystick__ is not None:
            return self.__joystick__.get_axis(number)
        return 0.0

    def bot_message(self, text):
        self.__display__.blit(self.textBox, (0, 360))
        self.__display__.blit(self.font.render(text, True, (255, 255, 255)), (150, 390))
        self.__display__.blit(self.fontSpace.render("[SPACE]", True, (255, 255, 255)), (560, 440))
        pg.display.flip()

    def set_visibility(self, tilex, tiley, value):
        self.visibility_data[tilex][tiley] = value
        self.update_fov = True

    def draw_fov(self):
        for x in range(len(self.fov_data)):
            for y in range(len(self.fov_data[0])):
                if self.fov_data[x][y]:
                    newx, newy = self.camera.transform_xy(x * TILE_SIZE, y * TILE_SIZE)
                    pg.draw.rect(self.__display__, (200, 200, 200), pg.Rect(newx, newy,
                                                                            TILE_SIZE, TILE_SIZE), 1)