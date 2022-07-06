# shop.py
from platform import node
from turtle import window_width
from venv import create
import pygame
from support import import_folder
from game_data import levels
from decoration import Sky
from settings import screen_height, screen_width

class Slot(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.pos = pos
        self.image = pygame.image.load('../graphics/shop/empty_wooden_slot.png').convert_alpha()
        self.rect = self.image.get_rect(center = pos)

    def update(self):
        self.rect.center = self.pos

class ShopBanner(Slot):
    def __init__(self, pos, surface):
        super().__init__(pos)
        self.display_surface = surface
        self.width, self.height = self.rect.width, self.rect.height
        self.image = pygame.transform.smoothscale(self.image, (self.width * 3, self.height * 1.5))
        self.rect = self.image.get_rect(center = pos)
        self.font = pygame.font.Font('../graphics/ui/ARCADEPI.ttf', 100)
        self.shop_surf = self.font.render("SHOP", False, '#33323d')
        self.shop_rect = self.shop_surf.get_rect(center = (self.rect.centerx, self.rect.centery))

    def update(self):
        self.rect.center = self.pos
        self.display_surface.blit(self.shop_surf, self.shop_rect)

class ShopItem(pygame.sprite.Sprite):
    def __init__(self, surface, amount, slot_pos, path_to_item_image):
        super().__init__()
        self.display_surface = surface
        self.font = pygame.font.Font('../graphics/ui/ARCADEPI.ttf', 30)
        self.amount = amount
        self.slot_pos = slot_pos
        self.slot_posX, self.slot_posY = slot_pos
        self.path = path_to_item_image
        self.image = pygame.image.load(self.path).convert_alpha()
        self.pos = (200 + self.slot_posX * 350, 200 + self.slot_posY * 200)
        self.coin_pos = (315 + self.slot_posX * 350, 200 + self.slot_posY * 200)

        self.coin = pygame.image.load('../graphics/ui/coin.png').convert_alpha()
        self.coin_rect = self.coin.get_rect(center = self.coin_pos)
        print(self.coin_pos)

        self.rect = self.image.get_rect(center=self.pos)
        # size should be no greater than 60x60

        self.coin_amount_surf = self.font.render(str(amount), False, '#33323d')
        self.coin_amount_rect = self.coin_amount_surf.get_rect(center = (self.coin_rect.right - 65, self.coin_rect.centery))
        
    def update(self):
        self.display_surface.blit(self.coin, self.coin_rect)
        self.display_surface.blit(self.coin_amount_surf, self.coin_amount_rect)

class Shop:
    def __init__(self, surface, coins, remove_coins, create_overworld, owned_items, max_level):
        #setup
        self.coins = coins
        self.remove_coins = remove_coins
        self.display_surface = surface
        self.max_level = max_level
        self.setup_shop_items()
        self.create_overworld = create_overworld
        self.font = pygame.font.Font('../graphics/ui/ARCADEPI.ttf', 30)

        #sprites 
        self.sky = Sky(8, 'overworld')

        self.items = pygame.sprite.Group()
        self.owned_items = owned_items

        ### ADD SHOP ITEMS HERE ###
        ### format: self.add_shop_item(amount, slot_pos, path_to_item_image)
        self.add_shop_item(30, (0,1), '../graphics/items/red_potion.png') # 3
        self.add_shop_item(20, (0,0), '../graphics/items/teal_potion.png') # 0
        self.add_shop_item(10, (1,0), '../graphics/items/mint_potion.png') # 1
        self.add_shop_item(10, (2,0), '../graphics/items/light_blue_potion.png') # 2
        self.add_shop_item(10, (0,2), '../graphics/items/watermelon.png') # 6
        self.add_shop_item(10, (1,1), '../graphics/items/rocket_boots.png') # 4

        # item manager
        self.item_manager = ItemManager(self.display_surface, self.owned_items)

        # time
        self.start_time = pygame.time.get_ticks()
        self.allow_input = False
        self.timer_length = 300

    def setup_shop_items(self):
        self.slot = pygame.sprite.Group()
        start_x = 250
        start_y = 200
        for y in range(3):
            for x in range(3):
                slot_sprite = Slot((start_x + x * 350, start_y + y * 200))
                self.slot.add(slot_sprite)
        
        self.banner = pygame.sprite.GroupSingle()
        self.banner_sprite = ShopBanner((screen_width // 2, 75), self.display_surface)
        self.banner.add(self.banner_sprite)
    
    def add_shop_item(self, amount, slot_num, path_to_item_image):
        new_item = ShopItem(self.display_surface, amount, slot_num, path_to_item_image)
        self.items.add(new_item)

    def show_coins(self, amount):
        self.display_surface.blit(self.coin, self.coin_rect)
        coin_amount_surf = self.font.render(str(amount), False, '#33323d')
        coin_amount_rect = coin_amount_surf.get_rect(midleft = (self.coin_rect.right + 4, self.coin_rect.centery))
        self.display_surface.blit(coin_amount_surf, coin_amount_rect)

    def input(self):
        #mouse = pygame.mouse.get_pressed()
        if pygame.mouse.get_pressed()[0]:
            if self.allow_input:
                self.allow_input = False
                self.start_time = pygame.time.get_ticks()
                mouseX, mouseY = pygame.mouse.get_pos()
                for index, slot in enumerate(self.slot):
                    if slot.rect.collidepoint(mouseX, mouseY):
                        for item in self.items:
                            if (item.slot_posX + item.slot_posY * 3) == index and item.amount <= self.coins and sum(n is not None for n in self.owned_items) <= 5:
                                self.owned_items = self.item_manager.add_item(item.path)
                                self.remove_coins(item.amount)
                                self.coins -= item.amount
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            print(f"Shop Scope owned items:{self.owned_items}")
            print(f"Item Manager Scope owned items:{self.item_manager.owned_items}")
            self.create_overworld(0, self.max_level, self.owned_items)

    def input_timer(self):
        if not self.allow_input:
            current_time = pygame.time.get_ticks()
            if current_time - self.start_time >= self.timer_length:
                self.allow_input = True

    def run(self):
        self.input_timer()
        self.input()
        self.item_manager.update(self.owned_items)
        #self.update_icon_pos()
        self.slot.update()
        #self.nodes.update()

        self.sky.draw(self.display_surface)
        #self.draw_paths()
        #self.nodes.draw(self.display_surface)
        self.slot.draw(self.display_surface)
        self.items.draw(self.display_surface)
        self.banner.draw(self.display_surface)
        self.banner.update()
        self.items.update()

class ItemManager():
    def __init__(self, surface, owned_items):
        # setup
        self.owned_items = owned_items
        self.display_surface = surface

        # slots
        self.item_slot_image = pygame.image.load('../graphics/items/empty_slots_good.png').convert_alpha()
        self.item_slot_pos = (screen_width//2, screen_height - 50)
        self.item_slot_rect = self.item_slot_image.get_rect(center = self.item_slot_pos)
        
        # surfs
        self.create_item_surfs()

    def create_item_surfs(self):   
        # item surfs
        self.owned_items_surf = []
        for item in self.owned_items:
            if item is not None:
                self.owned_items_surf.append(pygame.image.load(item).convert_alpha())

    def draw_items_in_slot(self):
        for index, item_surf in enumerate(self.owned_items_surf):
            if item_surf is not None:
                self.display_surface.blit(item_surf, (self.item_slot_rect.left + index * 110 + 50, self.item_slot_rect.centery - 30))
    
    def draw_slots(self):
        self.display_surface.blit(self.item_slot_image, self.item_slot_rect)
    
    def remove_item(self, item_index):
        self.owned_items_surf[item_index] = None
        self.owned_items[item_index] = None
        return self.owned_items
    
    def add_item(self, new_item_path):
        if len(self.owned_items) > 0:
            print("Adding item non zero")
            for index, item in enumerate(self.owned_items):
                #print(item)
                if item is None:
                    print("Replacing None")
                    self.owned_items[index] = new_item_path
                    break
            else:
                self.owned_items.append(new_item_path)
        elif len(self.owned_items) == 0:
            print("Adding item from zero")
            self.owned_items.append(new_item_path)
        print(self.owned_items)
        return self.owned_items
    
    def draw(self):
        self.draw_items_in_slot()
        self.draw_slots()
    
    def update(self, owned_items):
        self.owned_items = owned_items
