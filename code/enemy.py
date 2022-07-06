import pygame
from tiles import AnimatedTile
from random import randint

class Enemy(AnimatedTile):
    def __init__(self, size, x, y):
        super().__init__(size, x, y, '../graphics/enemy/run')
        self.rect.y += size - self.image.get_size()[1]
        ## CHANGE : this speed is a random number between 3 and 5, increase or decrease to change difficulty
        self.speed = randint(2, 8)
        self.freeze_speed = 1
        self.freeze_potion = False
    
    def freeze_speed_boost(self, start_time):
        if self.freeze_potion:
            current_time = pygame.time.get_ticks()
            if current_time - start_time >= 3000:
                self.freeze_potion = False
                self.freeze_speed = 1
                
    
    def move(self):
        self.rect.x += self.speed * self.freeze_speed
    
    def reverse_image(self):
        if self.speed > 0:
            self.image = pygame.transform.flip(self.image, True, False)
    
    def reverse(self):
        self.speed *= -1 * self.freeze_speed
    
    def update(self, shift):
        self.rect.x += shift
        self.animate()
        self.move()
        self.reverse_image()
