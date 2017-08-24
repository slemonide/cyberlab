import pygame

from game.settings import *
from ui.menu import main_menu


def main():
    pygame.init()
    pygame.joystick.init()
    display = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    main_menu(display).run()


if __name__ == '__main__':
    main()
