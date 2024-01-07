import pygame
from pygame import mixer #imports music and sound effects
import os #python function to count list of files automatically
import random 
import csv
import button

mixer.init() #like pygame, mixer needs to be initialized
pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8) #height will be the width x 0.8 -- it'll also be an integer so i have to put int

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Shooter')

#set framerate
clock = pygame.time.Clock()
FPS = 60

#game variables
GRAVITY = 0.75
SCROLL_THRESHOLD = 200 #the limit is 200px on the edge, so if it is detected then it'll move
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
MAX_LEVELS = 3
screen_scroll = 0
bg_scroll = 0
level = 1
start_game = False
start_intro = False

#define player action variables // all of these r false until the key is pressed
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False

#load music and sounds
pygame.mixer.music.load('audio/Laufey.mp3')
pygame.mixer.music.set_volume(0.05)
pygame.mixer.music.play(-1, 0.0, 5000) #-1 means it will loop indefinitely ~ 0.0 means it will loop instantly ~ duration of faded in ms
jump_fx = pygame.mixer.Sound('audio/boink.wav')
jump_fx.set_volume(0.5)
shoot_fx = pygame.mixer.Sound('audio/pew.wav')
shoot_fx.set_volume(0.5)
grenade_fx = pygame.mixer.Sound('audio/boom.wav')
grenade_fx.set_volume(0.5)


#load images
"""Button"""
start_img = pygame.image.load('img/button/start.png').convert_alpha()
exit_img = pygame.image.load('img/button/exit.png').convert_alpha()
restart_img = pygame.image.load('img/button/restart.png').convert_alpha()
"""Background"""
tree_img = pygame.image.load('img/background/tree.png').convert_alpha()
tree2_img = pygame.image.load('img/background/tree2.png').convert_alpha()
mountain_img = pygame.image.load('img/background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/background/sky.png').convert_alpha()

#stores the tiles in a list
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'img/Tile/{x}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE)) #tile size for x and y
    img_list.append(img)
bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()
grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()
health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/grenade_box.png').convert_alpha()
item_boxes = {
    'Health'    : health_box_img,
    'Ammo'      : ammo_box_img,
    'Grenade'   : grenade_box_img
}

#define colors
BG = (232, 238, 241) 
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

#define the font
font = pygame.font.SysFont('Futura', 30)


def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


def draw_bg(): #the background 
    screen.fill(BG)
    width = sky_img.get_width()
    for x in range(5): #it'll be shown 5 times so it doesnt run out 
        screen.blit(sky_img, ((x * width)- bg_scroll * 0.5, 0))
        screen.blit(mountain_img, ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
        screen.blit(tree_img, ((x * width) - bg_scroll * 0.7, SCREEN_HEIGHT - tree_img.get_height() - 150))
        screen.blit(tree2_img, ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - tree2_img.get_height()))  

#function to reset the level - basically erases everything in case something is taken or if an enemy is killed blabla
def reset_level():
    enemy_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()

    #create empty tile list
    data = []
    for row in range(ROWS):
        r = [-1] * COLS #creates a list of 150 entries of -1 ~ for the map
        data.append(r)
    return data

class Soldier(pygame.sprite.Sprite): #basically makes it easier to make more players or enemies :>
    def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.ammo = ammo
        self.start_ammo = ammo
        self.shoot_cooldown = 0
        self.grenades = grenades
        self.health = 100
        self.max_health = self.health 
        self.direction = 1 
        self.vel_y = 0 #starts w 0
        self.jump = False #currently stationary
        self.in_air = True
        self.flip = False #so the character can flip direction from facing left to right n vice versa
        self.animation_list = []
        self.frame_index = 0 #point of which the animation is at -- in this case it starts at 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        #the ai's specific variables
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20) #creating a rect that scopes the ai's vision so they can sort of look for the player to X_X them
        self.idling = False
        self.idling_counter = 0


        #loads all animations for the players
        animation_types = ['Idle', 'Run', 'Jump', 'Death']
        for animation in animation_types:
            #resets temporary list of animations
            temp_list = []
            #counts the number of files in the folder
            num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}')) #creates a list of items in that directory
            for i in range(num_of_frames):
                img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png') #self.char_type pushes whatever character type folder i have in the img folder
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale))) #takes the existing img width n height to make it the same size as the scale
                temp_list.append(img)
            self.animation_list.append(temp_list) 

        self.image = self.animation_list[self.action][self.frame_index]
        self. rect = self.image.get_rect() #creates a rectangle containing^ 
        self.rect.center = (x, y) #position of rect follows x y
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.update_animation()
        self.check_alive()
        #update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1


    def move(self, moving_left, moving_right):
        #reset movement variables
        screen_scroll = 0
        dx = 0
        dy = 0
        #assign movement variables if moving left/right
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        """#jump n gravity"""
        if self.jump == True and self.in_air == False: 
            self.vel_y = -12
            self.jump = False
            self.in_air = True
        
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y
        dy += self.vel_y #y velcotiy will be changed and affeected by gravity

        #checks collision w the floor
        for tile in world.obstacle_list:
            #checks collision in the x direction
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                #if the ai hits a wall, he'll turn around
                if self.char_type == 'enemy':
                    self.direction *= -1
                    self.move_counter = 0
            #checks collision in the y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                #check if below the ground ~ jumping
                if self.vel_y < 0: #the head hits something bok benjol
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top #max amt of distance allowed to move spya ga nembus 
                #checks if above the ground ~ falling
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom
        
        #checks for collision with the water
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0 #so when it collides w water, dia mati x_x
        
        #checks for collision with the exit sign at the end
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True
        
        #checks if the player falls off the map lol noob do parkour
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0
                
        #checks if the player is going off the screen
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0 #ensures he doesnt get out of the map lol
 
        #update the position
        self.rect.x += dx if not self.in_air else dx * 0.8
        self.rect.y += dy
        #update scroll based on the character's current position
        if self.char_type == 'player':                       #'so this makes sure it doesnt scroll too far and fits the screen width    
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESHOLD and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH) \
                or (self.rect.left < SCROLL_THRESHOLD and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx #whatever dx is, the screen moves to the opposite direction of dx
        return screen_scroll, level_complete
                

    
    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20 #starts at 0 turns to 20
            bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
            bullet_group.add(bullet) 
            #reduce ammo
            self.ammo -= 1
            shoot_fx.play()

    def ai(self):
        if self.alive and player.alive:
            if self.idling == False and random.randint(1, 150) == 1: #gives a random integer for an action to be carried out
                self.update_action(0)#0 is Idle
                self.idling = True
                self.idling_counter = 50 #counters so it stays idle for a small amount of time only
            #checks if the ai is near the player
            if self.vision.colliderect(player.rect):
                #stops running and faces the player
                self.update_action(0) #so it goes idle again and thennnn
                self.shoot()#it starts shooting :D
            else:
                if self.idling == False:
                    if self.direction == 1: #facing right
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right #always going to be the inverse
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)#1 is Run
                    self.move_counter += 1
                    #update ai vision whilst the enemy is moving
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False
                
        self.rect.x += screen_scroll


    def update_animation(self):
        #updates animation
        ANIMATION_COOLDOWN = 100
        #update image depending on current frame
        self.image = self.animation_list[self.action][self.frame_index]
        #checks if enough time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        #if animation has run out, loop back to start
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    def update_action(self, new_action):
        #checks if the new action sama kyk yg sblmny
         if new_action != self.action: #not equal to
            self.action = new_action #this basically ensures that the new action is updated
            #update the animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect) #blit is one of the methods to place an image onto the screens of pygame applications
                                                                #^false so the character doesnt turn upside down


class World():
    def __init__(self):
        self.obstacle_list = []
    
    def process_data(self, data): #takes the argument of self and data to be used
        self.level_length = len(data[0])

        #iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect() 
                    img_rect.x = x * TILE_SIZE #x position 
                    img_rect.y = y * TILE_SIZE #y position 
                    tile_data = (img, img_rect)

                    if tile >= 0 and tile <= 8:
                        self.obstacle_list.append(tile_data)

                    elif tile >= 9 and tile <= 10:
                        """Water"""
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water) 

                    elif tile >= 11 and tile <= 14:
                        """grass, wooden boxes, piles of rocks"""
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration) 
                    elif tile == 15:
                        """creating the player"""
                        player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 1.65, 5, 20, 5)
                        health_bar = HealthBar(10, 10, player.health, player.health)
                    elif tile == 16: 
                        """creating the enemies"""
                        enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 1.65, 2, 20, 0)
                        enemy_group.add(enemy)
                    elif tile == 17:
                        """creating the ammo power up"""
                        item_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box) 
                    elif tile == 18:
                        """creating the grenade up"""
                        item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box) 
                    elif tile == 19:
                        """creating the health power up"""
                        item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box) 
                    elif tile == 20: 
                        """The exit"""
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit) 

        return player, health_bar
    
    def draw(self): #blits every tile so it pops up when played
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1]) #the image is 0 and the rect is 1

class Decoration(pygame.sprite.Sprite):
    def __init__ (self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    
    def update(self):
        self.rect.x += screen_scroll #ensures that everything in this class has an absolute position so it doesnt fly around

class Water(pygame.sprite.Sprite):
    def __init__ (self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    
    def update(self):
        self.rect.x += screen_scroll #ensures that everything in this class has an absolute position so it doesnt fly around

class Exit(pygame.sprite.Sprite):
    def __init__ (self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    
    def update(self):
        self.rect.x += screen_scroll #ensures that everything in this class has an absolute position so it doesnt fly around

class ItemBox(pygame.sprite.Sprite):
    def __init__ (self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    
    def update(self):
        #scroll
        self.rect.x += screen_scroll #ensures that the character comes across the power ups and this makes sure they dont move around
        #check if the player has picked up the box
        if pygame.sprite.collide_rect(self, player):
            #checks what kind of box it was
            if self.item_type == 'Health':
                player.health += 25
                if player.health > player.max_health:
                    player.health = player.max_health
            elif self.item_type == 'Ammo':
                player.ammo += 25
            elif self.item_type == 'Grenade':
                player.grenades += 3
            #deletes the box after UDAH DAPETTTTT ADUH CAPEKKKKKKKKKKKKKKKKKKKKK
            self.kill()


class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health
        
    def draw(self, health):
        #updates with new health
        self.health = health
        #calculate health ratio
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))

        
class Bullet(pygame.sprite.Sprite):
    def __init__ (self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        #move bullet
        self.rect.x += (self.direction * self.speed) + screen_scroll #screen scroll so the bullets dont go too fast when the screen is scrolling
        #checks if the bullets have gone off the map
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        #check for collision with level
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill() #removes the bullets when they hit a block

        #checks collision with enemy
        if pygame.sprite.spritecollide(player, bullet_group, False):
            if player.alive:
                player.health -= 5
                self.kill()
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    enemy.health -= 25
                    self.kill()


class Grenade(pygame.sprite.Sprite):
    def __init__ (self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100
        self.vel_y = -11 #trajectory of the projectile
        self.speed = 7
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.direction = direction
    
    def update(self): #we need to control the vel_y for gravity so the grenade falls down after being shot up, and the horizontal speed
        self.vel_y += GRAVITY #changes the y velocity variable
        dx = self.direction * self.speed #change in the x coordinate of the grenade - determined by speed and direction of the grenade
        dy = self.vel_y

        #checks for collision with level
        for tile in world.obstacle_list:
            #checks collision with the walls
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1
                dx = self.direction * self.speed
            #checks collision in the y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                self.speed = 0 #this is so the grenade doesnt start sliding whenever it's on the floor
                #check if below the ground ~ thrown up
                if self.vel_y < 0: #the grenade hits the top and is bounced
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top #max amt of distance allowed to move spya ga nembus 
                #checks if above the ground ~ falling
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom

        
        #update grenade position
        self.rect.x += dx + screen_scroll
        self.rect.y += dy

        #countdown timer
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            grenade_fx.play()
            explosion = Explosion(self.rect.x, self.rect.y, 0.5)
            explosion_group.add(explosion)
            #do damage to the grenade's surroundings
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
                player.health -= 50
            for enemy in enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
                    enemy.health -= 50
                    


class Explosion(pygame.sprite.Sprite):
    def __init__ (self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 6):
            img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0
    
    def update(self):
        #scroll
        self.rect.x += screen_scroll #ensures the explosion doesnt move around when the screen is scrolling
        EXPLOSION_SPEED = 4
        #update explosion animation
        self.counter += 1

        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            #if the animation is complete then deletes the explosion
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]

class ScreenFade():
    def __init__(self, direction, color, speed):
        self.direction = direction
        self.color = color
        self.speed = speed
        self.fade_counter = 0

    #transitions from screen --- the cool effects :>
    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed
        if self.direction == 1: #whole screen fade
            pygame.draw.rect(screen, self.color, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT)) #rectangle slowly moves to the left
            pygame.draw.rect(screen, self.color, (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))#as the fade increases the rect moves to the right
            pygame.draw.rect(screen, self.color, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
            pygame.draw.rect(screen, self.color, (0, SCREEN_HEIGHT // 2 + self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))
        if self.direction == 2: #vertical screen fade down
            pygame.draw.rect(screen, self.color, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter)) #x and y starts at 0, width = screen width
        if self.fade_counter >= SCREEN_WIDTH:
            fade_complete = True

        return fade_complete

#you win popup
class Popup(pygame.sprite.Sprite):
    def __init__(self, x, y, text, font):
        pygame.sprite.Sprite.__init__(self)
        self.font = font
        self.image = self.font.render(text, True, BG)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def draw(self, screen):
        screen.blit(self.image, self.rect)





#create screen fades
intro_fade = ScreenFade(1, BLACK, 4)
death_fade = ScreenFade(2, BG, 4)

#creates buttons
start_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_img, 1)
exit_button = button.Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_img, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_img, 2)

#the sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()


#create empty tile list
world_data = []
for row in range(ROWS):
    r = [-1] * COLS #creates a list of 150 entries of -1 ~ for the map
    world_data.append(r)
#loads the level data and makes the world design
with open(f'level{level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',') #delimiter tells us where each of these individual values changes to another ~ the comma so aft every comma theres a diff new value
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data) #the player and health bar will be returned

run = True
win_popup = None 
level_complete = False
all_enemies_defeated = False
player_reached_exit = False
while run:

    clock.tick(FPS)

    if start_game == False:
        #main menu
        screen.fill(BG)
        #add buttons
        if start_button.draw(screen):
            start_game = True
            start_intro = True
        if exit_button.draw(screen):
            run = False

    else:
        #update bg
        draw_bg()
        #draws the world map and its tiles
        world.draw()
        #show player health
        health_bar.draw(player.health)
        #shows the amt of ammo
        draw_text(f'AMMO: ', font, WHITE, 10, 35)
        for x in range(player.ammo):
            screen.blit(bullet_img, (90 + (x * 10), 40))
        #shows the amt of grenades
        draw_text(f'GRENADES: ', font, WHITE, 10, 60)
        for x in range(player.grenades):
            screen.blit(grenade_img, (135 + (x * 15), 60))
    

        player.update()
        player.draw()

        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw() 

        #update and draw the groups
        bullet_group.update()
        grenade_group.update()
        explosion_group.update()
        item_box_group.update()
        water_group.update()
        decoration_group.update()
        exit_group.update()
        bullet_group.draw(screen)
        grenade_group.draw(screen)
        explosion_group.draw(screen)
        item_box_group.draw(screen)
        water_group.draw(screen)
        decoration_group.draw(screen)
        exit_group.draw(screen)

        #show intro
        if start_intro == True:
            if intro_fade.fade():
                start_intro = False #makes sure it's only run 1 time
                intro_fade.fade_counter = 0

        #update player actions
        if player.alive:
            #shoot bullets
            if shoot:
                player.shoot()
            #throw grenades
            elif grenade and grenade_thrown == False and player.grenades > 0:
                grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction), 
                            player.rect.top, player.direction)
                grenade_group.add(grenade)
                #reduce grenades
                player.grenades -= 1
                grenade_thrown = True
                
            if player.in_air:
                player.update_action(2) #2 is jumping animation
            elif moving_left or moving_right:
                player.update_action(1) #1 is the running animation
            else:
                player.update_action(0)#0 refers it back to the idle animation
            screen_scroll, level_complete = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll #tracks overall how much the screen has scrolled

            #checks if the current level has been completed
            if level_complete:
                start_intro = True
                level += 1
                bg_scroll = 0
                world_data = reset_level()
                if level <= MAX_LEVELS:
                   #loads the level data and makes the world design
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',') #delimiter tells us where each of these individual values changes to another ~ the comma so aft every comma theres a diff new value
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data) #the player and health bar will be returned
 
        else:
            screen_scroll = 0
            if death_fade.fade(): #when player dies the color fade comes in 
                if restart_button.draw(screen):
                    death_fade.fade_counter = 0
                    start_intro = True
                    bg_scroll = 0 #putting everything back to the start
                    world_data = reset_level()
                    #loads the level data and makes the world design
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',') #delimiter tells us where each of these individual values changes to another ~ the comma so aft every comma theres a diff new value
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data) #the player and health bar will be returned
        
    #makes sure all enemies r ded
    if len(enemy_group) == 0:
        all_enemies_defeated = True
    
    if pygame.sprite.spritecollide(player, exit_group, False):
        player_reached_exit = True
    
    #checks if the player's reached the exit
    if all_enemies_defeated and player_reached_exit: 
        level_complete = True

    #after level 2, a YOU WIN popup appears
    if level_complete and level > 2: 
        win_popup = Popup(SCREEN_WIDTH // 2, SCREEN_HEIGHT //2, "YOU WIN!", font)
    
    if win_popup:
        win_popup.draw(screen)




    for event in pygame.event.get():
        #quit game
        if event.type == pygame.QUIT:
            run = False
        #when key r pressed
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a: #moves when a is pressed
                moving_left = True
            if event.key == pygame.K_d: #moves when d is pressed
                moving_right = True
            if event.key == pygame.K_SPACE:
                shoot = True
            if event.key == pygame.K_q:
                grenade = True 
            if event.key == pygame.K_w and player.alive: #jump whoop
                player.jump = True
                jump_fx.play()
            if event.key == pygame.K_ESCAPE:
                run = False #quits game when esc is pressed

        #when key r released
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a: #stops moving when a is released
                moving_left = False
            if event.key == pygame.K_d: #stops moving when d is released
                moving_right = False
            if event.key == pygame.K_SPACE:
                shoot = False
            if event.key == pygame.K_q:
                grenade = False
                grenade_thrown = False

    pygame.display.update() #ensures the image pops up from screen blit

pygame.quit()