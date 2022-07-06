#levels.py

import pygame
from tiles import Tile, StaticTile, Crate, Coin, Palm, Heart
from decoration import Sky, Water, Clouds
from enemy import Enemy
from settings import tile_size, screen_width, screen_height
from player import Player
from particles import ParticleEffect
from support import import_csv_layout, import_cut_graphics
from player import Player, Dragon
from particles import ParticleEffect
from game_data import levels
from random import randint
from shop import ItemManager

class Level:
    def __init__(self, current_level, surface, create_overworld, change_coins, change_health, owned_items):

        #general setup
        self.display_surface = surface
        self.world_shift = 0
        self.current_x = None

        # audio
        self.coin_sound = pygame.mixer.Sound('../audio/effects/coin.wav')
        self.stomp_sound = pygame.mixer.Sound('../audio/effects/stomp.wav')

        #overworld connection
        self.create_overworld = create_overworld
        self.current_level = current_level
        level_data = levels[self.current_level]
        self.new_max_level = level_data['unlock']

        # projectiles
        self.projectiles = pygame.sprite.GroupSingle()
        self.dragon_projectiles = pygame.sprite.GroupSingle()

        #active player
        self.active_player = 'player'

        #player
        player_layout = import_csv_layout(level_data['player'])
        self.player = pygame.sprite.GroupSingle()
        self.goal = pygame.sprite.GroupSingle()
        self.player_setup(player_layout, change_health)

        #transport sprites
        self.transport_layout = import_csv_layout(level_data['transport'])
        self.dragon = pygame.sprite.GroupSingle()
        self.change_health = change_health
        self.dragon_created = False
        self.dragon_x, self.dragon_y = self.get_dragon_starting_position(self.transport_layout)
        #self.dragon_setup(transport_layout, change_health)

        #user interface
        self.change_coins = change_coins
        self.change_health = change_health

        #dust
        self.dust_sprite = pygame.sprite.GroupSingle()
        self.player_on_ground = False

        #explosion particles
        self.explosion_sprites = pygame.sprite.Group()

        #terrain setup
        terrain_layout = import_csv_layout(level_data['terrain'])
        self.terrain_sprites = self.create_tile_group(terrain_layout, 'terrain')

        #grass setup
        grass_layout = import_csv_layout(level_data['grass'])
        self.grass_sprites = self.create_tile_group(grass_layout, 'grass')

        #crates setup
        crate_layout = import_csv_layout(level_data['crates'])
        self.crate_sprites = self.create_tile_group(crate_layout, 'crates')

        #coins
        coin_layout = import_csv_layout(level_data['coins'])
        self.coin_sprites = self.create_tile_group(coin_layout, 'coins')

        #foreground palms
        fg_palm_layout = import_csv_layout(level_data['fg palms'])
        self.fg_palm_sprites = self.create_tile_group(fg_palm_layout, 'fg palms')

        #background palms
        bg_palm_layout = import_csv_layout(level_data['bg palms'])
        self.bg_palm_sprites = self.create_tile_group(bg_palm_layout, 'bg palms')

        # enemy
        enemy_layout = import_csv_layout(level_data['enemies'])
        self.enemy_sprites = self.create_tile_group(enemy_layout, 'enemies')

        # constraint
        constraint_layout = import_csv_layout(level_data['constraints'])
        self.constraint_sprites = self.create_tile_group(constraint_layout, 'constraint')

        # jump boost platforms
        jump_boost_platforms_layout = import_csv_layout(level_data['jump_boost'])
        self.jump_boost_sprites = self.create_tile_group(jump_boost_platforms_layout, 'jump_boost')

        #decoration
        self.sky = Sky(8)
        level_width = len(terrain_layout[0]) * tile_size
        self.water = Water(screen_height - 25, level_width)
        self.clouds = Clouds(400, level_width, 30)

        # hearts 
        self.heart_sprites = pygame.sprite.Group()

        # items
        self.owned_items = owned_items
        self.item_manager = ItemManager(self.display_surface, self.owned_items)
        self.invincibility_potion = False
        self.invincibility_boost_start_time = 0
        self.running_speed_boost_start_time = 0
        self.gravity_boost_start_time = 0
        self.freeze_start_time = 0
    
    def create_tile_group(self, layout, type):
        sprite_group = pygame.sprite.Group()
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                if val != '-1':
                    x = col_index * tile_size
                    y = row_index * tile_size

                    if type == 'terrain':
                        terrain_tile_list = import_cut_graphics('../graphics/terrain/terrain_tiles.png')
                        tile_surface = terrain_tile_list[int(val)]
                        sprite = StaticTile(tile_size, x, y, tile_surface)
                    if type == 'grass':
                        grass_tile_list = import_cut_graphics('../graphics/decoration/grass/grass.png')
                        tile_surface = grass_tile_list[int(val)]
                        sprite = StaticTile(tile_size, x, y, tile_surface)
                    if type == 'crates':
                        sprite = Crate(tile_size, x, y)
                    if type == 'coins':
                        if val == '0': sprite = Coin(tile_size, x, y, '../graphics/coins/gold', 5)
                        if val == '1': sprite = Coin(tile_size, x, y, '../graphics/coins/silver', 1)
                    if type == 'fg palms':
                        if val == '0': sprite = Palm(tile_size, x, y, '../graphics/terrain/palm_small', 38)
                        if val == '1': sprite = Palm(tile_size, x, y, '../graphics/terrain/palm_large', 64)
                    if type == 'bg palms':
                        sprite = Palm(tile_size, x, y, '../graphics/terrain/palm_bg', 38)
                    if type == 'enemies':
                        sprite = Enemy(tile_size, x, y)
                    if type == 'constraint':
                        sprite = Tile(tile_size, x, y)
                    if type == 'jump_boost':
                        sprite = Tile(tile_size, x, y)
                    try:
                        sprite_group.add(sprite)
                    except:
                        print(f'No tile of type {type} found in layout.')
        return sprite_group
    
    def player_setup(self, layout, change_health):
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                x = col_index * tile_size
                y = row_index * tile_size
                if val == '0':
                    sprite = Player((x, y), self.display_surface, self.create_jump_particles, change_health)
                    projectile_sprite = sprite.projectile.sprite
                    self.projectiles.add(projectile_sprite)
                    self.player.add(sprite)
                if val == '1':
                    hat_surface = pygame.image.load('../graphics/character/hat.png').convert_alpha()
                    sprite = StaticTile(tile_size, x, y, hat_surface)
                    self.goal.add(sprite)

    def dragon_setup(self, layout, change_health):
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                x = col_index * tile_size
                y = row_index * tile_size
                if val == '0':
                    #sprite = Player((x, y), self.display_surface, self.create_jump_particles, change_health)
                    sprite = Dragon((x, y), self.display_surface, change_health)
                    self.dragon.add(sprite)
                    projectile_sprite = sprite.projectile.sprite
                    self.dragon_projectiles.add(projectile_sprite)
                if val == '1':
                    hat_surface = pygame.image.load('../graphics/character/hat.png').convert_alpha()
                    sprite = StaticTile(tile_size, x, y, hat_surface)
                    self.goal.add(sprite)
    
    def get_dragon_starting_position(self, layout):
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                x = col_index * tile_size
                y = row_index * tile_size
                if val == '0':
                    dragon_position_x = x
                    dragon_position_y = y
        return dragon_position_x, dragon_position_y

    def jump_boost_platform(self):
        if self.player_on_ground and pygame.sprite.spritecollide(self.player.sprite, self.jump_boost_sprites.sprites(), False):
            #print("JUMP BOOST")
            self.player.sprite.set_jump_boost()
        elif self.player_on_ground:
            pass
            #self.player.sprite.set_default_jump()
    
    def enemy_collision_reverse(self):
        for enemy in self.enemy_sprites.sprites():
            if pygame.sprite.spritecollide(enemy, self.constraint_sprites, False):
                enemy.reverse()

    def create_jump_particles(self, pos):
        if self.player.sprite.facing_right:
            pos -= pygame.math.Vector2(10,5)
        else:
            pos += pygame.math.Vector2(10,5)
        jump_particle_sprite = ParticleEffect(pos, 'jump')
        self.dust_sprite.add(jump_particle_sprite)
    
    def horizontal_movement_collision(self):
        if self.active_player == 'player':
            player = self.player.sprite
        elif self.active_player == 'dragon':
            player = self.dragon.sprite

        player.collision_rect.x += player.direction.x * player.speed

        collidable_sprites = self.terrain_sprites.sprites() + self.crate_sprites.sprites() + self.fg_palm_sprites.sprites()

        for sprite in collidable_sprites:
            if sprite.rect.colliderect(player.collision_rect):
                if player.direction.x < 0:
                    player.collision_rect.left = sprite.rect.right
                    player.on_left = True
                elif player.direction.x > 0:
                    player.collision_rect.right = sprite.rect.left
                    player.on_right = True

    def vertical_movement_collision(self):
        if self.active_player == 'player':
            player = self.player.sprite
            player.apply_gravity()
        elif self.active_player == 'dragon':
            player = self.dragon.sprite
            player.collision_rect.y += player.direction.y * player.speed

        collidable_sprites = self.terrain_sprites.sprites() + self.crate_sprites.sprites() + self.fg_palm_sprites.sprites()
        jump_boost_sprites = self.jump_boost_sprites.sprites()

        if self.active_player == 'player':
            for sprite in jump_boost_sprites:
                if sprite.rect.colliderect(player.collision_rect):
                    if player.direction.y > 0:
                        player.collision_rect.bottom = sprite.rect.top
                        player.direction.y = 0
                        player.on_ground = True
                        player.set_jump_boost()

        for sprite in collidable_sprites:
            if sprite.rect.colliderect(player.collision_rect):
                if player.direction.y > 0:
                    player.collision_rect.bottom = sprite.rect.top
                    player.direction.y = 0
                    player.on_ground = True
                    if self.active_player == 'player':
                        player.set_default_jump()
                elif player.direction.y < 0:
                    player.collision_rect.top = sprite.rect.bottom
                    player.direction.y = 0
                    player.on_ceiling = True
        
        if self.dragon_created == True:
            if self.active_player == 'player' and self.dragon.sprite.rect.colliderect(player):
                player.collision_rect.bottom = self.dragon.sprite.rect.top
                player.direction.y = 0
                player.on_dragon = True
                self.dragon.sprite.active = True
                self.active_player = 'dragon'
                print("IM ON THE DRAGON")

        if player.on_ground and player.direction.y < 0 or player.direction.y > 1:
            player.on_ground = False

    def scroll_x(self):
        if self.active_player == 'player':
            player = self.player.sprite
        elif self.active_player == 'dragon':
            player = self.dragon.sprite
        player_x = player.rect.centerx
        direction_x = player.direction.x

        if player_x < screen_width / 4 and direction_x < 0:
            self.world_shift = 8 + player.boost_speed
            player.speed = 0
        elif player_x > screen_width - (screen_width / 4) and direction_x > 0:
            self.world_shift = -8 - player.boost_speed
            player.speed = 0
        else:
            self.world_shift = 0
            player.speed = 8 + player.boost_speed

    def get_player_on_ground(self):
        if self.player.sprite.on_ground:
            self.player_on_ground = True
        else:
            self.player_on_ground = False
    
    def create_landing_dust(self):
        if not self.player_on_ground and self.player.sprite.on_ground and not self.dust_sprite.sprites():
            if self.player.sprite.facing_right:
                offset = pygame.math.Vector2(10, 15)
            else:
                offset = pygame.math.Vector2(10, 15)
            fall_dust_particle = ParticleEffect(self.player.sprite.rect.midbottom - offset, 'land')
            self.dust_sprite.add(fall_dust_particle)

    def check_death(self):
        if self.player.sprite.rect.top > screen_height:
            self.create_overworld(self.current_level, 0, self.owned_items)
    
    def check_win(self):
        if pygame.sprite.spritecollide(self.player.sprite, self.goal, False):
            self.create_overworld(self.current_level, self.new_max_level, self.owned_items)

    def check_coin_collisions(self):
        if self.active_player == 'player':
            player = self.player.sprite
        elif self.active_player == 'dragon':
            player = self.dragon.sprite
        collided_coins = pygame.sprite.spritecollide(player, self.coin_sprites, True)
        if collided_coins:
            self.coin_sound.play()
            for coin in collided_coins:
                self.change_coins(coin.value)

    def check_heart_collisions(self):
        if self.active_player == 'player':
            player = self.player.sprite
        elif self.active_player == 'dragon':
            player = self.dragon.sprite
        collided_hearts = pygame.sprite.spritecollide(player, self.heart_sprites, True)
        if collided_hearts:
            for heart in collided_hearts:
                self.change_health(heart.value)
    
    def check_loot_crate(self):
        if self.active_player == 'player':    
            fireball_collisions = pygame.sprite.spritecollide(self.projectiles.sprite, self.crate_sprites, False)
            player = self.player.sprite
        elif self.active_player == 'dragon':
            fireball_collisions = pygame.sprite.spritecollide(self.dragon_projectiles.sprite, self.crate_sprites, False)
            player = self.dragon.sprite
        if fireball_collisions and player.shot is True:
            for crate in fireball_collisions:
                explosion_sprite = ParticleEffect(crate.rect.center, 'explosion')
                print(f"Crate Center: {crate.rect.center}")
                self.explosion_sprites.add(explosion_sprite)
                self.player.sprite.shot = False
                self.add_random_sprite(crate.rect.centerx, crate.y)
                crate.kill()
    
    def add_random_sprite(self, x, y):
        random_choice = randint(0, 2)

        if random_choice == 0:
            new_coin_sprite = Coin(tile_size, x, y, '../graphics/coins/gold', 5)
            self.coin_sprites.add(new_coin_sprite)
        elif random_choice == 1:
            new_enemy_sprite = Enemy(tile_size, x, y)
            self.enemy_sprites.add(new_enemy_sprite)
        elif random_choice == 2:
            new_heart_sprite = Heart(tile_size, x, y, 10)
            self.heart_sprites.add(new_heart_sprite)
        #This one is for you Kai, just change the code to at the top of this function to  random_choice = 3
        elif random_choice == 3:
            #Change the number in range( ) to a bigger one for more enemies, keep it reasonable though, otherwise the game might crash
            for i in range(25):
                new_enemy_sprite = Enemy(tile_size, x, y)
                self.enemy_sprites.add(new_enemy_sprite)

    def check_enemy_collisions(self):
        if self.active_player == 'player':    
            enemy_collisions = pygame.sprite.spritecollide(self.player.sprite, self.enemy_sprites, False)
            fireball_collisions = pygame.sprite.spritecollide(self.projectiles.sprite, self.enemy_sprites, False)
            player = self.player.sprite
        elif self.active_player == 'dragon':
            enemy_collisions = pygame.sprite.spritecollide(self.dragon.sprite, self.enemy_sprites, False)
            fireball_collisions = pygame.sprite.spritecollide(self.dragon_projectiles.sprite, self.enemy_sprites, False)
            player = self.dragon.sprite

        if enemy_collisions:
            for enemy in enemy_collisions:
                enemy_center = enemy.rect.centery
                enemy_top = enemy.rect.top
                player_bottom = self.player.sprite.rect.bottom
                if enemy_top < player_bottom < enemy_center and self.player.sprite.direction.y >= 0:
                    self.stomp_sound.play()
                    self.player.sprite.direction.y = -15
                    explosion_sprite = ParticleEffect(enemy.rect.center, 'explosion')
                    self.explosion_sprites.add(explosion_sprite)
                    enemy.kill()
                else:
                    if not self.player.sprite.invincibility_potion:
                        self.player.sprite.get_damage()
                    if self.dragon_created:
                        if not self.dragon.sprite.invincible:
                            print("Get damage dragon")
                            self.dragon.sprite.get_damage()
        
        if fireball_collisions and player.shot is True:
            for enemy in fireball_collisions:
                self.stomp_sound.play()
                explosion_sprite = ParticleEffect(enemy.rect.center, 'explosion')
                self.explosion_sprites.add(explosion_sprite)
                enemy.kill()
                self.player.sprite.shot = False

    def get_input(self):
        keys = pygame.key.get_pressed()

        if self.active_player == 'dragon' and keys[pygame.K_SPACE]:
            self.active_player = 'player'
            self.player.sprite.on_dragon = False
            self.dragon.sprite.active = False
            self.player.sprite.jump()

        try:
            if keys[pygame.K_1] and self.item_manager.owned_items[0] != None:
                self.apply_powerup(self.item_manager.owned_items[0])
                self.owned_items = self.item_manager.remove_item(0)
            if keys[pygame.K_2] and self.item_manager.owned_items[1] != None:
                self.apply_powerup(self.item_manager.owned_items[1])
                self.owned_items = self.item_manager.remove_item(1)
            if keys[pygame.K_3] and self.item_manager.owned_items[2] != None:
                self.apply_powerup(self.item_manager.owned_items[2])
                self.owned_items = self.item_manager.remove_item(2)
            if keys[pygame.K_4] and self.item_manager.owned_items[3] != None:
                self.apply_powerup(self.item_manager.owned_items[3])
                self.owned_items = self.item_manager.remove_item(3)
            if keys[pygame.K_5] and self.item_manager.owned_items[4] != None:
                self.apply_powerup(self.item_manager.owned_items[4])
                self.owned_items = self.item_manager.remove_item(4)
            if keys[pygame.K_6] and self.item_manager.owned_items[5] != None:
                self.apply_powerup(self.item_manager.owned_items[5])
                self.owned_items = self.item_manager.remove_item(5)
                for enemy in self.enemy_sprites.sprites():
                    enemy.freeze_speed = 0
        except IndexError:
            pass
    
    def apply_powerup(self, item_path):
        if item_path.endswith("rocket_boots.png"):
            self.player.sprite.gravity_potion = True
            self.player.sprite.gravity = 0.4
            self.gravity_boost_start_time = pygame.time.get_ticks()
        if item_path.endswith("light_blue_potion.png"):
            self.freeze_start_time = pygame.time.get_ticks()
            for enemy in self.enemy_sprites.sprites():
                enemy.freeze_potion = True
                enemy.freeze_speed = 0
        if item_path.endswith("red_potion.png"):
            self.player.sprite.invincible = True
            self.player.sprite.invincibility_potion = True
            self.invincibility_boost_start_time = pygame.time.get_ticks()
        if item_path.endswith("watermelon.png"):
            self.change_health(10)
        if item_path.endswith("dark_blue_potion.png"):
            self.player.sprite.boost_speed = 8
            self.player.sprite.running_speed_potion = True
            self.running_speed_boost_start_time = pygame.time.get_ticks()
        if item_path.endswith("teal_potion.png"):
            sprite = Dragon((self.dragon_x, self.dragon_y), self.display_surface, self.change_health)
            self.dragon.add(sprite)
            projectile_sprite = sprite.projectile.sprite
            self.dragon_projectiles.add(projectile_sprite)
            self.dragon_created = True

    def equate_positions(self):
        if self.active_player == 'dragon':
            self.player.sprite.rect.centerx = self.dragon.sprite.rect.centerx
            self.player.sprite.rect.centery = self.dragon.sprite.rect.centery - 30

    def run(self):
        #decoration
        self.sky.draw(self.display_surface)
        self.clouds.draw(self.display_surface, self.world_shift)

        #background palms
        self.bg_palm_sprites.update(self.world_shift)
        self.bg_palm_sprites.draw(self.display_surface)

        #dust particles
        self.dust_sprite.update(self.world_shift)
        self.dust_sprite.draw(self.display_surface)

        #terrain
        self.terrain_sprites.draw(self.display_surface)
        self.terrain_sprites.update(self.world_shift)

        #enemy
        self.enemy_sprites.update(self.world_shift)
        self.constraint_sprites.update(self.world_shift)
        self.enemy_collision_reverse()
        self.enemy_sprites.draw(self.display_surface)
        self.explosion_sprites.update(self.world_shift)
        self.explosion_sprites.draw(self.display_surface)

        #crate
        self.crate_sprites.update(self.world_shift)
        self.crate_sprites.draw(self.display_surface)
        self.check_loot_crate()

        # hearts
        self.heart_sprites.update(self.world_shift)
        self.heart_sprites.draw(self.display_surface)

        # grass
        self.grass_sprites.update(self.world_shift)
        self.grass_sprites.draw(self.display_surface)

        #coins 
        self.coin_sprites.update(self.world_shift)
        self.coin_sprites.draw(self.display_surface)

        #foreground palms
        self.fg_palm_sprites.update(self.world_shift)
        self.fg_palm_sprites.draw(self.display_surface)

        #player sprites
        self.jump_boost_sprites.update(self.world_shift)
        self.player.update()
        self.equate_positions()
        self.horizontal_movement_collision()
        self.get_player_on_ground()
        self.vertical_movement_collision()
        self.create_landing_dust()
        self.scroll_x()
        if self.dragon_created:
            if self.active_player == 'dragon':
                self.dragon.update()
            elif self.active_player == 'player':
                self.dragon.sprite.update_shift(self.world_shift)
            self.dragon.draw(self.display_surface)
        else:
            self.dragon_x += self.world_shift
        self.player.draw(self.display_surface)
        self.goal.update(self.world_shift)
        self.goal.draw(self.display_surface)

        self.check_death()
        self.check_win()
        self.player.sprite.invincibility_boost(self.invincibility_boost_start_time)
        self.player.sprite.running_speed_boost(self.running_speed_boost_start_time)
        self.player.sprite.gravity_boost(self.gravity_boost_start_time)
        if self.freeze_start_time != 0:
            for enemy in self.enemy_sprites.sprites():
                enemy.freeze_speed_boost(self.freeze_start_time)
        self.check_coin_collisions()
        self.check_enemy_collisions()
        self.check_heart_collisions()

        #water
        self.water.draw(self.display_surface, self.world_shift)

        # item slots
        self.item_manager.update(self.owned_items)
        self.get_input()
        self.item_manager.draw()