#player.py
import pygame
from support import import_folder, import_cut_graphics
from math import sin
from settings import screen_width

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, surface, create_jump_particles, change_health):
        super().__init__()
        self.import_character_assets()
        self.frame_index = 0
        self.animation_speed = 0.15
        self.image = self.animations['idle'][self.frame_index]
        self.rect = self.image.get_rect(topleft = pos)

        #dust particles
        self.import_dust_run_particles()
        self.dust_frame_index = 0
        self.dust_animation_speed = 0.15
        self.display_surface = surface
        self.create_jump_particles = create_jump_particles

        #player movement
        self.direction = pygame.math.Vector2(0,0)
        self.boost_speed = 0
        self.speed = 8
        self.gravity = 0.8
        self.jump_speed = -16
        self.collision_rect = pygame.Rect(self.rect.topleft, (50, self.rect.height))
        self.running_speed_potion = False
        self.gravity_potion = False

        #player status
        self.status = 'idle'
        self.facing_right = True
        self.on_ground = False
        self.on_ceiling = False
        self.on_left = False
        self.on_right = False
        self.on_dragon = False

        # health management
        self.change_health = change_health
        self.invincible = False
        self.invincibility_duration = 500
        self.hurt_time = 0
        self.invincibility_potion = False

        # projectiles 
        self.shot = False
        self.projectile = pygame.sprite.GroupSingle()
        self.fireball = FireBall()
        self.projectile.add(self.fireball)
        self.projectile_direction = True

        # audio
        self.jump_sound = pygame.mixer.Sound('../audio/effects/jump.wav')
        self.jump_sound.set_volume(0.8)
        self.hit_sound = pygame.mixer.Sound('../audio/effects/hit.wav')

    def import_character_assets(self):
        character_path = '../graphics/character/'
        self.animations = {'idle':[], 'run':[], 'jump':[], 'fall':[]}
        for animation in self.animations.keys():
            full_path = character_path + animation
            self.animations[animation] = import_folder(full_path)
    
    def import_dust_run_particles(self):
        self.dust_run_particles = import_folder('../graphics/character/dust_particles/run')
        print(len(self.dust_run_particles))

    def animate(self):
        animation = self.animations[self.status]

        #loop over frame index
        self.frame_index += self.animation_speed
        if self.frame_index >= len(animation):
            self.frame_index = 0
        
        image = animation[int(self.frame_index)]
        if self.facing_right:
            self.image = image
            self.rect.bottomleft = self.collision_rect.bottomleft
        else:
            flipped_image = pygame.transform.flip(image, True, False)
            self.image = flipped_image
            self.rect.bottomright = self.collision_rect.bottomright
        
        if self.invincible:
            alpha = self.wave_value()
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)
        
        self.rect = self.image.get_rect(midbottom = self.rect.midbottom)

    def run_dust_animation(self):
        if self.status == 'run' and self.on_ground:
            self.dust_frame_index += self.dust_animation_speed
            if self.dust_frame_index >= len(self.dust_run_particles):
                self.dust_frame_index = 0
            
            dust_particle = self.dust_run_particles[int(self.dust_frame_index)]
            if self.facing_right:
                pos = self.rect.bottomleft - pygame.math.Vector2(6,10)
                self.display_surface.blit(dust_particle, pos)
            else:
                pos = self.rect.bottomright - pygame.math.Vector2(6,10)
                flipped_dust_particle = pygame.transform.flip(dust_particle, True, False)
                self.display_surface.blit(flipped_dust_particle, pos)

    def get_input(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction.x = 1
            self.facing_right = True
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.direction.x = -1
            self.facing_right = False
        else:
            self.direction.x = 0
        
        if keys[pygame.K_SPACE] and self.on_ground:
            self.jump()
            self.create_jump_particles(self.rect.midbottom)
        elif keys[pygame.K_LSHIFT] and not self.shot and not self.on_dragon:  
            self.shoot()

    def get_status(self):
        if self.direction.y < 0:
            self.status = 'jump'
        elif self.direction.y > 1:
            self.status = 'fall'
        else:
            if self.direction.x != 0:
                self.status = 'run'
            else:
                self.status = 'idle'

    def apply_gravity(self):
        self.direction.y += self.gravity
        self.collision_rect.y += self.direction.y
    
    def jump(self):
        self.direction.y = self.jump_speed
        self.jump_sound.play()
    
    def set_jump_boost(self):
        self.jump_speed = -32
    
    def set_default_jump(self):
        self.jump_speed = -16
    
    def shoot(self):
        self.shot = True
        self.projectile_direction = self.facing_right
    
    def reset_projectile(self):
        if self.projectile.sprite.getX() >= screen_width or self.projectile.sprite.getX() < -1:
            self.shot = False

    def get_damage(self):
        if not self.invincible:
            self.hit_sound.play()
            self.change_health(-10)
            self.invincible = True
            self.hurt_time = pygame.time.get_ticks()

    def invincibility_timer(self):
        if self.invincible and not self.invincibility_potion:
            current_time = pygame.time.get_ticks()
            if current_time - self.hurt_time >= self.invincibility_duration:
                self.invincible = False
    
    def invincibility_boost(self, start_time):
        if self.invincible and self.invincibility_potion:
            current_time = pygame.time.get_ticks()
            if current_time - start_time >= 3000:
                self.invincible = False
                self.invincibility_potion = False
    
    def running_speed_boost(self, start_time):
        if self.running_speed_potion:
            current_time = pygame.time.get_ticks()
            if current_time - start_time >= 3000:
                self.boost_speed = 0
                self.running_speed_potion = False

    def gravity_boost(self, start_time):
        if self.gravity_potion:
            current_time = pygame.time.get_ticks()
            if current_time - start_time >= 3000:
                self.gravity = 0.8
                self.gravity_potion = False

    def wave_value(self):
        value = sin(pygame.time.get_ticks())
        if value >= 0: return 255
        else: return 0

    def update(self):
        if not self.on_dragon:
            self.projectile.update(self.shot, self.collision_rect.centerx, self.collision_rect.centery, self.projectile_direction)
        self.reset_projectile()
        self.get_input()
        self.get_status()
        self.animate()
        self.run_dust_animation()
        self.invincibility_timer()
        self.wave_value()
        if self.shot: self.projectile.draw(self.display_surface)


class FireBall(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.frame_index = 0
        self.animation_speed = 0.25
        self.animations = import_cut_graphics('../graphics/character/fire_bullets.png')
        self.original_image = self.animations[self.frame_index]
        self.flipped_image = pygame.transform.flip(self.original_image, True, False)
        self.image = self.original_image
        self.rect = self.image.get_rect(center = (0,0))
        self.speed = 10
        self.x = 0
        self.y = 0
    
    def getX(self):
        return self.x

    def animate(self, facingRight):
        animation = self.animations

        #loop over frame index
        self.frame_index += self.animation_speed
        if self.frame_index >= len(animation):
            self.frame_index = 0
        
        image = animation[int(self.frame_index)]
        if facingRight:
            self.image = image
            #self.rect.bottomleft = self.collision_rect.bottomleft
        else:
            flipped_image = pygame.transform.flip(image, True, False)
            self.image = flipped_image
            #self.rect.bottomright = self.collision_rect.bottomright
    
    def update(self, shot, playerCenterX, playerCenterY, facingRight):
        if not shot:
            self.rect = self.image.get_rect(center = (playerCenterX, playerCenterY))
            self.x = playerCenterX
            self.y = playerCenterY
        elif facingRight:
            self.animate(facingRight)
            #self.image = self.original_image
            self.x += self.speed
            self.rect = self.image.get_rect(center = (self.x, self.y))
        elif not facingRight:
            self.animate(facingRight)
            #self.image = self.flipped_image
            self.x -= self.speed
            self.rect = self.image.get_rect(center = (self.x, self.y))


class Dragon(pygame.sprite.Sprite):
    def __init__(self, pos, surface, change_health):
        super().__init__()
        self.import_character_assets()
        self.frame_index = 0
        self.animation_speed = 0.15
        self.image = self.animations[self.frame_index]
        self.rect = self.image.get_rect(topleft = pos)
        
        #dust particles
        #self.dust_frame_index = 0
        #self.import_dust_run_particles()
        #self.dust_animation_speed = 0.15
        self.display_surface = surface
        #self.create_jump_particles = create_jump_particles

        #dragon movement
        self.direction = pygame.math.Vector2(0,0)
        self.speed = 8
        self.boost_speed = 0
        self.gravity = 0.8
        self.jump_speed = -16
        self.collision_rect = pygame.Rect(self.rect.topleft, (self.rect.width - 10, self.rect.height))

        #dragon status
        self.status = 'idle'
        self.facing_right = True
        self.on_ground = False
        self.on_ceiling = False
        self.on_left = False
        self.on_right = False
        self.active = False

        # health management
        self.change_health = change_health
        self.invincible = False
        self.invincibility_duration = 500
        self.hurt_time = 0

        # projectiles 
        self.shot = False
        self.projectile = pygame.sprite.GroupSingle()
        self.fireball = FireBall()
        self.projectile.add(self.fireball)
        self.projectile_direction = True

        # audio
        # Add some wing flap sounds
        self.jump_sound = pygame.mixer.Sound('../audio/effects/jump.wav')
        self.jump_sound.set_volume(0.8)
        self.hit_sound = pygame.mixer.Sound('../audio/effects/hit.wav')

    def import_character_assets(self):
        dragon_path = '../graphics/dragon'
        self.animations = []
        self.dragon_image = import_folder(dragon_path)
        for image in self.dragon_image:
            self.animations.append(image)
    
    #def import_dust_run_particles(self):
    #    self.dust_run_particles = import_folder('../graphics/character/dust_particles/run')

    def animate(self):
        animation = self.animations

        #loop over frame index
        self.frame_index += self.animation_speed
        if self.frame_index >= len(animation):
            self.frame_index = 0
        
        image = animation[int(self.frame_index)]
        if self.facing_right:
            self.image = image
            self.rect.bottomleft = self.collision_rect.bottomleft
        else:
            flipped_image = pygame.transform.flip(image, True, False)
            self.image = flipped_image
            self.rect.bottomright = self.collision_rect.bottomright
        
        if self.invincible:
            alpha = self.wave_value()
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)
        
        self.rect = self.image.get_rect(midbottom = self.rect.midbottom)

    def run_dust_animation(self):
        if self.status == 'run' and self.on_ground:
            self.dust_frame_index += self.dust_animation_speed
            if self.dust_frame_index >= len(self.dust_run_particles):
                self.dust_frame_index = 0
            
            dust_particle = self.dust_run_particles[int(self.dust_frame_index)]
            if self.facing_right:
                pos = self.rect.bottomleft - pygame.math.Vector2(6,10)
                self.display_surface.blit(dust_particle, pos)
            else:
                pos = self.rect.bottomright - pygame.math.Vector2(6,10)
                flipped_dust_particle = pygame.transform.flip(dust_particle, True, False)
                self.display_surface.blit(flipped_dust_particle, pos)

    def get_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction.x = 1
            self.facing_right = True
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.direction.x = -1
            self.facing_right = False
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            self.direction.y = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.direction.y = 1
        else:
            self.direction.x = 0
            self.direction.y = 0
        
        #if keys[pygame.K_SPACE] and self.on_ground:
            #self.active = False
            #self.jump()
            #self.create_jump_particles(self.rect.midbottom)
        if keys[pygame.K_LSHIFT]:
            self.shoot()

    def shoot(self):
        self.shot = True
        self.projectile_direction = self.facing_right
    
    def reset_projectile(self):
        if self.projectile.sprite.getX() >= screen_width or self.projectile.sprite.getX() < -1:
            self.shot = False

    def get_status(self):
        if self.direction.y < 0:
            self.status = 'jump'
        elif self.direction.y > 1:
            self.status = 'fall'
        else:
            if self.direction.x != 0:
                self.status = 'run'
            else:
                self.status = 'idle'

    def apply_gravity(self):
        self.direction.y += self.gravity
        self.collision_rect.y += self.direction.y
    
    def jump(self):
        self.direction.y = self.jump_speed
        self.jump_sound.play()

    def get_damage(self):
        if not self.invincible:
            self.hit_sound.play()
            self.change_health(-10)
            self.invincible = True
            self.hurt_time = pygame.time.get_ticks()

    def invincibility_timer(self):
        if self.invincible:
            current_time = pygame.time.get_ticks()
            if current_time - self.hurt_time >= self.invincibility_duration:
                self.invincible = False

    def wave_value(self):
        value = sin(pygame.time.get_ticks())
        if value >= 0: return 255
        else: return 0
    
    def dismount_player():
        return True

    def update_shift(self, shift):
        if not self.active: self.rect.x += shift
    def update(self):
        self.get_input()
        if self.active:
            self.projectile.update(self.shot, self.collision_rect.centerx, self.collision_rect.centery, self.projectile_direction)
        self.reset_projectile()
        #self.get_status()
        self.animate()
        #self.run_dust_animation()
        self.invincibility_timer()
        self.wave_value()
        if self.shot: self.projectile.draw(self.display_surface)