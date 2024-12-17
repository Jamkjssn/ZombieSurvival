import pygame
import sys
import math
import random
from settings import *

pygame.init()

# Create game window first
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zombie Survival")
clock = pygame.time.Clock()

# Load in the game background
background = pygame.image.load("background/background(0).png")
plain_background = pygame.image.load("background/black.png")

#Create the Player Class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Default starting location
        self.pos = pygame.math.Vector2(PLAYER_START_X, PLAYER_START_Y)
        # Set player image/size
        self.image = pygame.transform.rotozoom(pygame.image.load("player/0.png").convert_alpha(), 0, PLAYER_SIZE)
        self.base_player_image = self.image
        # Initialize hitbox and location rect
        self.hitbox_rect = self.base_player_image.get_rect(center = self.pos)
        self.rect = self.hitbox_rect.copy()
        # Set Player Speed
        self.speed = PLAYER_SPEED
        # Start not shooting
        self.shoot = False
        # Shoot cooldown starts at 0
        self.shoot_cooldown = 0
        # Set gun location offset so bullets dont come from center of character 
        self.gun_barrel_offset = pygame.math.Vector2(GUN_OFFSET_X, GUN_OFFSET_Y)
        # Set Player Health
        self.health = 100

        self.strong = False
        
        # Add the player to the sprites group
        newGame.all_sprites_group.add(self)

    def player_rotation(self):
        # Get mouse position
        self.mouse_coords = pygame.mouse.get_pos()
        # Calculate angle between player and mouse
        self.angle = math.degrees(math.atan2((self.mouse_coords[1] - (HEIGHT//2)), (self.mouse_coords[0] - (WIDTH//2))))
        # Rotate player image accordingly
        self.image = pygame.transform.rotate(self.base_player_image, -self.angle)
        # Update rect to match new image position
        self.rect = self.image.get_rect(center = self.hitbox_rect.center)

    def player_input(self):
        self.velocity_x = 0
        self.velocity_y = 0

        keys = pygame.key.get_pressed()

        # W key moves up
        if keys[pygame.K_w]:
            self.velocity_y = -self.speed

        # A key moves left
        if keys[pygame.K_a]:
            self.velocity_x = -self.speed

        # S key moves down
        if keys[pygame.K_s]:
            self.velocity_y = self.speed

        # D key moves right
        if keys[pygame.K_d]:
            self.velocity_x = self.speed

        # Diagonal movement needs to be the same speed as horizontal/vertical movement
        if self.velocity_x != 0 and self.velocity_y != 0:
            self.velocity_x /= math.sqrt(2)
            self.velocity_y /= math.sqrt(2)

        # Click to shoot
        if pygame.mouse.get_pressed() == (1, 0, 0):
            self.shoot = True
            self.is_shooting()
        else:
            self.shoot = False

        # Debugging Get coordinates
        if pygame.mouse.get_pressed() == (0, 0, 1):
            if self.shoot_cooldown == 0:
                newGame.big_wave = True
                self.strong = True
                self.shoot_cooldown = 1000                   
                print(f"Player Position: {self.pos}")
                print(f"Mouse Position: {self.mouse_coords}")

    
    def is_shooting(self):
        # Shooting cooldown is at zero, so time to shoot
        if self.shoot_cooldown == 0:
            # First reset cooldown
            if self.strong == True:
                self.shoot_cooldown = NO_SHOOT_COOLDOWN
            else:
                self.shoot_cooldown = SHOOT_COOLDOWN
            # Set spawnpoint for bullet
            spawn_bullet_pos = self.pos +  self.gun_barrel_offset.rotate(self.angle)
            # Create bullet
            self.bullet = Bullet(spawn_bullet_pos[0], spawn_bullet_pos[1], self.angle)
            # Add bullet to list of bullets
            newGame.bullet_group.add(self.bullet)
            # Add bullet to list of all sprites
            newGame.all_sprites_group.add(self.bullet)

    def move(self):
        # Check for collisions and move player
        self.hitbox_rect.centerx += self.velocity_x
        self.collision_check("horizontal")        
        
        self.hitbox_rect.centery += self.velocity_y
        self.collision_check("vertical")

        # Make sure hitbox and image location are both moving as well
        self.rect.center = self.hitbox_rect.center
        self.pos = self.hitbox_rect.center

    def collision_check(self, direction):
        for sprite in newGame.obstacles_group:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == "horizontal":
                    if self.velocity_x > 0:
                        self.hitbox_rect.right = sprite.rect.left
                    if self.velocity_x < 0:
                        self.hitbox_rect.left = sprite.rect.right

                if direction == "vertical":
                    if self.velocity_y < 0:
                        self.hitbox_rect.top = sprite.rect.bottom
                    if self.velocity_y > 0:
                        self.hitbox_rect.bottom = sprite.rect.top


    def update(self):
        # Get current keys
        self.player_input()
        # Update the player's position and velocity
        self.move()
        self.player_rotation()
        # Update shooting cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        # Initialize bullet image
        self.image = pygame.image.load("bullet/1.png").convert_alpha()
        self.image = pygame.transform.rotozoom(self.image, 0, BULLET_SCALE)
        # Initialize bullet position and hitbox
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.x = x
        self.y = y
        # Initialize bullet velocity
        self.speed = BULLET_SPEED
        # Good ol' trigonometry to get velocity vector
        self.x_vel = math.cos(math.radians(angle)) * self.speed
        self.y_vel = math.sin(math.radians(angle)) * self.speed
        # Finite bullet lifetime to prevent lag buildup
        self.bullet_lifetime = BULLET_LIFETIME
        # Get the time it spawns so we can despawn it later
        self.spawn_time = pygame.time.get_ticks()

    def bullet_movement(self):
        # Move the bullet based on velocity
        self.x += self.x_vel
        self.y += self.y_vel

        # update hitbox position to match bullet
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        if pygame.time.get_ticks() - self.spawn_time > self.bullet_lifetime:
            # If lifetime is longer than BULLET_LIFETIME, despawn the bullet
            self.kill()

    def bullet_collisions(self): 
        # Check for collision with enemies

        hits = pygame.sprite.groupcollide(newGame.enemy_group, newGame.bullet_group, False, True)

        for hit in hits:
            hit.health -= 10
        
        wall_hit =  pygame.sprite.spritecollide(self, newGame.obstacles_group, False) # wall collisions
        if wall_hit:
            self.kill()
        for wall in wall_hit:
            wall.take_damage(10)

    def update(self):
        # Update bullet
        self.bullet_movement()
        self.bullet_collisions()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position):
        super().__init__(newGame.enemy_group, newGame.all_sprites_group)
        # Initilaize position
        self.pos = pygame.math.Vector2(position[0], position[1])

        # Initialize enemy image
        self.image = pygame.image.load("Enemy/baseZombie/Base_Image/zombie.png").convert_alpha()
        self.image = pygame.transform.rotozoom(self.image, 0, ENEMY_SCALE)
        self.base_image = self.image

        # Setup hitbox
        self.hitbox_rect = self.image.get_rect(center = self.pos)      ## Might have to copy method of line 22 in example for this to work but we'll see
        self.rect = self.hitbox_rect.copy()
        
        # Initialize direction, speed, and velocity
        self.direction = pygame.math.Vector2()
        self.speed = ENEMY_SPEED
        self.velocity = pygame.math.Vector2()

        # Attack cooldown starts at 0
        self.attack_cooldown = 0

        # Health starts at 100
        self.health = 100

        # Add enemy to groups
        newGame.all_sprites_group.add(self)
        newGame.enemy_group.add(self)
        
    def hunt_player(self):
        # Get the player and enemy positions
        player_vector = pygame.math.Vector2(player.hitbox_rect.center)
        enemy_vector = pygame.math.Vector2(self.rect.center)
        # Calculate distance between them
        distance = self.get_vector_distance(player_vector, enemy_vector)

        # Always move towards the player, dont have time for a more complicated AI
        if distance > 1:
            self.direction = (player_vector - enemy_vector).normalize()
        else:
            self.direction = pygame.math.Vector2(0, 0)
        
        # Update location using direction and speed
        self.velocity = self.direction * self.speed
        self.pos += self.velocity

        # Update rect/hitbox to match position
        self.hitbox_rect.center = self.pos
        self.rect.center = self.pos

    
    def rotate_enemy(self):
        # Rotate enemy to face the player
        #First get player location
        self.x_change = (self.direction.x)
        self.y_change = (self.direction.y)
        self.angle = math.degrees(math.atan2(self.y_change, self.x_change))
        self.image = pygame.transform.rotate(self.base_image, -self.angle)  
        self.rect = self.image.get_rect(center = self.hitbox_rect.center)        

    def get_vector_distance(self, vector_1, vector_2):
        # Just a helper to get the distance between vectors
        return (vector_1 - vector_2).magnitude()
    
    def is_attacking(self):
        # Tries to attack if collision with player
        if self.attack_cooldown <= 0:
            # Check if player is in hitbox
            if self.rect.colliderect(player.hitbox_rect):
                # Attack player
                player.take_damage(ENEMY_DAMAGE)
                self.attack_cooldown = ENEMY_ATTACK_COOLDOWN # Reset cooldown to 60 frames (1 second)
    
    def draw_health(self):
        # Draw health bar
        # Green for above 2/3 health
        if self.health > 66:
            col = (0, 255, 0)
        # Yellow for 1/3 to 2/3 health
        elif self.health > 33:
            col = (255, 255, 0)
        # Red for below 1/3 health
        else:
            col = (255, 0, 0)

        width = int((self.hitbox_rect.width - 20) * self.health / 100)
        pygame.draw.rect(screen, col, ((self.hitbox_rect.centerx - 45 - newGame.offset.x), (self.hitbox_rect.top + 3 - newGame.offset.y), width, 5))

    def check_life(self):
        # I guess enemies are supposed to die?
        if self.health <= 0:
            self.kill()

    def update(self):
        # Update enemy
    
        self.draw_health()
        self.check_life()
        self.hunt_player()
        self.rotate_enemy()

        # Update attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

# Object Class
class Objects(pygame.sprite.Sprite):
    def __init__(self, position):
        super().__init__()
        # we dont want to spawn it inside of things
        # Load and set up the box sprite
        self.image = pygame.image.load("object/box.png").convert_alpha()
        self.image = pygame.transform.rotozoom(self.image, 0, 4)
        self.rect = self.image.get_rect()
        self.rect.center = position

        # Check for collisions with other objects
        for obj in newGame.all_sprites_group:
            if self.rect.colliderect(obj.rect):
                # If a collision is detected, remove the object and stop initialization
                self.kill()
                return

        # If no collision, add to the appropriate group
        newGame.all_sprites_group.add(self)
        newGame.obstacles_group.add(self)

        self.rect.center = (position[0], position[1])
        self.health = 100
        self.moveable = False

        newGame.all_sprites_group.add(self)
        newGame.obstacles_group.add(self)
    
    def update(self):
        # Update object
        self.draw_health()
        if self.moveable:
            self.push_on_collision()

    def take_damage(self, amount):
        # Subtract damage from the object
        self.health -= amount
        # If the objects health falls below 40 it can be moved
        if self.health <= 40:
            self.moveable = True
        # If the objects health falls below 0, kill it.
        if self.health <= 0:
            self.kill()
        
    def push_on_collision(self):
        # For each sprite in the all_sprites_group, check if it's colliding with this object
        for obj in newGame.all_sprites_group:
            if obj != self and self.rect.colliderect(obj.rect):
                # Calculate the direction to push the object
                push_vector = pygame.Vector2(self.rect.centerx - obj.rect.centerx, self.rect.centery - obj.rect.centery)
                push_distance = 5  # How much to move the object on collision (adjust as needed)
                push_vector = push_vector.normalize() * push_distance
                
                # Move the object away from the other object to "push" it
                self.rect.x += push_vector.x
                self.rect.y += push_vector.y

    def draw_health(self):
        # Draw health bar
        # Green for above 2/3 health
        if self.health > 66:
            col = (0, 255, 0)
        # Yellow for 1/3 to 2/3 health
        elif self.health > 33:
            col = (255, 255, 0)
        # Red for below 1/3 health
        else:
            col = (255, 0, 0)

        width = int((self.rect.width - 20) * self.health / 100)
        pygame.draw.rect(screen, col, ((self.rect.centerx - 50 - newGame.offset.x), (self.rect.top - 11 - newGame.offset.y), width, 5))

# Contains game logic as well as camera movement
class Game(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.offset = pygame.math.Vector2()
        self.floor_rect = background.get_rect(topleft = (0,0))
        self.box_spawn_cooldown = BOX_SPAWN
        self.zombie_spawn_cooldown = ENEMY_SPAWN
        self.last_zombie_spawn = pygame.time.get_ticks()
        self.last_box_spawn = pygame.time.get_ticks()
        self.all_sprites_group = pygame.sprite.Group()
        self.bullet_group = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()
        self.obstacles_group = pygame.sprite.Group()
        self.big_wave = False
        self.wave_length = 2000
        self.wave_start = pygame.time.get_ticks()
        self.max_zombies = 10
        self.current_wave = False

    def spawn_enemy(self):
        # Spawn a zombie at a random position on the map
        position = random.randint(928, 2910), random.randint(323, 1987)
        newZombie = Enemy(position)
        # self.enemy_group.add(newZombie)

    def spawn_object(self):
        # Spawn a zombie at a random position on the map
        position = random.randint(928, 2910), random.randint(323, 1987)
        newBox = Objects(position)
        # self.obstacles_group.add(newBox)

    def update(self):
        current_time = pygame.time.get_ticks()

        # Check if its time to spawn a box
        if current_time - self.last_box_spawn >= self.box_spawn_cooldown and len(self.obstacles_group) < 5:
            self.spawn_object()
            self.last_box_spawn = current_time

        # check if its time to spawn a zombie
        if current_time - self.last_zombie_spawn >= self.zombie_spawn_cooldown and len(self.enemy_group) < self.max_zombies:
            self.spawn_enemy()
            self.last_zombie_spawn = current_time

        # Secret Big Wave
        if self.big_wave:
            for _ in range(5):
                self.spawn_enemy()
            self.big_wave = False
            self.wave_start = current_time
            self.current_wave = True
            # Increase zombie count and spawn rate during the wave
            self.zombie_spawn_cooldown = 100
            self.max_zombies = 40

        # Spawning surge for big wave
        if self.current_wave:
            if current_time - self.wave_start >= self.wave_length:
                # End of wave, reset values
                self.zombie_spawn_cooldown = ENEMY_SPAWN
                self.max_zombies = 10
                self.current_wave = False

        # Update all sprites
        self.all_sprites_group.update()


    def custom_draw(self):
        self.offset.x = player.rect.centerx - WIDTH//2
        self.offset.y = player.rect.centery - HEIGHT//2

        #Draw floor
        floor_offset_pos = self.floor_rect.topleft - self.offset
        screen.blit(background, floor_offset_pos)

        for sprite in newGame.all_sprites_group:
            offset_pos = sprite.rect.topleft - self.offset
            screen.blit(sprite.image, offset_pos)

# Initilaize Player and Game
newGame = Game()
player = Player()


while True:
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit() 
    
    # Update game each tick
    screen.blit(plain_background, (0, 0))

    # Use game class to update and draw game
    newGame.custom_draw()
    newGame.update()

    pygame.display.update()
    clock.tick(FPS)