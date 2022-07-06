import pygame
import sys
from settings import *
from tiles import Tile
from level import Level
from overworld import Overworld
from ui import UI
from shop import Shop

# Game Class is used to switch the game between the levels and the overworld
class Game:
    def __init__(self):
        ## Attributes declared here will remain regardless of game state (level vs overworld)
        ## these are the starting values
        #game attributes
        self.max_level = 0
        self.max_health = 100
        self.cur_health = 100
        self.coins = 0

        # audio
        self.level_bg_music = pygame.mixer.Sound('../audio/level_music.wav')
        self.overworld_bg_music = pygame.mixer.Sound('../audio/overworld_music.wav')

        # items
        self.owned_items = []

        # overworld creation
        self.overworld = Overworld(0, self.max_level, screen, self.create_level, self.coins, self.create_shop, self.owned_items)
        self.status = 'overworld'
        self.overworld_bg_music.play(loops = -1)

        # user interface
        self.ui = UI(screen)

    def create_level(self, current_level, owned_items):
        self.level = Level(current_level, screen, self.create_overworld, self.change_coins, self.change_health, owned_items)
        self.status = 'level'
        self.overworld_bg_music.stop()
        self.level_bg_music.play(loops = -1)
    
    def create_overworld(self, current_level, new_max_level, owned_items):
        if new_max_level > self.max_level:
            self.max_level = new_max_level
        self.overworld = Overworld(current_level, self.max_level, screen, self.create_level, self.coins, self.create_shop, owned_items)
        self.status = 'overworld'
        self.level_bg_music.stop()
        self.overworld_bg_music.stop()
        self.overworld_bg_music.play(loops = -1)
    
    def create_shop(self, coins, surface, owned_items, max_level):
        self.shop = Shop(surface, coins, self.remove_coins, self.create_overworld, owned_items, max_level)
        self.overworld_bg_music.stop()
        self.overworld_bg_music.play(loops = -1)
        self.status = 'shop'

    def change_coins(self, amount):
        self.coins += amount
    
    def remove_coins(self, amount):
        self.coins -= amount

    def change_health(self, amount):    
        self.cur_health += amount

    def check_game_over(self, owned_items):
        if self.cur_health <= 0:
            self.cur_health = self.max_health
            self.coins = 0
            self.max_level = 0
            self.overworld = Overworld(0, self.max_level, screen, self.create_level, self.coins, self.create_shop, owned_items)
            self.status = 'overworld'
            self.level_bg_music.stop()
            self.overworld_bg_music.play(loops = -1)

    def run(self):
        if self.status == 'overworld':
            self.overworld.run()
        elif self.status == 'shop':
            self.shop.run()
            self.ui.show_coins(self.coins)
        else:
            self.level.run()
            self.ui.show_health(self.cur_health, self.max_health)
            self.ui.show_coins(self.coins)
            self.check_game_over(self.owned_items)

pygame.init()

pygame.event.set_allowed([pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN, pygame.KEYUP])

screen = pygame.display.set_mode((screen_width, screen_height))

clock = pygame.time.Clock()

game = Game()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    

    screen.fill('black')
    game.run()
    pygame.display.update()
    clock.tick(60)