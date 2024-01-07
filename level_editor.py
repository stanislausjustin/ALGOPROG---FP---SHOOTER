import pygame
import button
import csv

pygame.init()

clock = pygame.time.Clock()
FPS = 60

#game window
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 640
LOWER_MARGIN = 100
SIDE_MARGIN = 300

screen = pygame.display.set_mode((SCREEN_WIDTH + SIDE_MARGIN, SCREEN_HEIGHT + LOWER_MARGIN))
pygame.display.set_caption('Level Editor')

#defining the game variables
ROWS = 16
MAXIMUM_COLUMNS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
level = 0
current_tile = 0
scroll_left = False
scroll_right = False
scroll = 0
scroll_speed = 1


#load images
tree_img = pygame.image.load('img/background/tree.png').convert_alpha()
tree2_img = pygame.image.load('img/background/tree2.png').convert_alpha()
mountain_img = pygame.image.load('img/background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/background/sky.png').convert_alpha()
#store tiles in a list
img_list = []
for i in range(TILE_TYPES):
    img = pygame.image.load(f'img/Tile/{i}.png').convert_alpha()
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)

save_img = pygame.image.load('img/editor/save.png').convert_alpha()
load_img = pygame.image.load('img/editor/load.png').convert_alpha()

WHITE = (232, 238, 241)
WHITE2 = (255, 255, 255)
RED = (200, 25, 25)

#define font
font = pygame.font.SysFont('Futura', 30)


#creating the empty tile list
world_data = []
for row in range(ROWS):
    r = [-1] * MAXIMUM_COLUMNS
    world_data.append(r)

#creates ground
for tile in range(0, MAXIMUM_COLUMNS):
    world_data[ROWS - 1][tile] = 0 

#function for outputting text onto the screen
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))



"""creates the function to draw the bg"""
def draw_bg():
    screen.fill(WHITE)
    width = sky_img.get_width()
    for x in range(4):
        screen.blit(sky_img, ((x * width) - scroll * 0.5, 0))
        screen.blit(mountain_img, ((x * width) - scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
        screen.blit(tree_img, ((x * width) - scroll * 0.7, SCREEN_HEIGHT - tree_img.get_height() - 150))
        screen.blit(tree2_img, ((x * width) - scroll * 0.8, SCREEN_HEIGHT - tree2_img.get_height()))


"""draws the grid"""
def draw_grid():
    #vertical lines
    for x in range(MAXIMUM_COLUMNS + 1):
        pygame.draw.line(screen, WHITE2, (x * TILE_SIZE - scroll, 0), (x * TILE_SIZE - scroll, SCREEN_HEIGHT))
    #horizontal lines
    for x in range(ROWS + 1):
        pygame.draw.line(screen, WHITE2, (0, x * TILE_SIZE) , (SCREEN_WIDTH, x * TILE_SIZE))

#function for drawing the world tiles
def draw_world(): #going to iterate with a for loop
    for y, row in enumerate(world_data):
        for x, tile in enumerate (row):
            if tile >= 0:
                screen.blit(img_list[tile], (x * TILE_SIZE - scroll, y * TILE_SIZE))



#create buttons
save_button = button.Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT + LOWER_MARGIN - 50, save_img, 1)
load_button = button.Button(SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT + LOWER_MARGIN - 50, load_img, 1)
#makes a button list
button_list = []
button_col = 0
button_row = 0
for y in range(len(img_list)):
    tile_button = button.Button(SCREEN_WIDTH + (75 * button_col) + 50, 75 * button_row + 50, img_list[y], 1)
    button_list.append(tile_button)
    button_col += 1
    if button_col == 3:
        button_row += 1
        button_col = 0


run = True
while run:

    clock.tick(FPS)

    draw_bg()
    draw_grid()
    draw_world()

    draw_text(f'Level: {level}', font, RED, 10, SCREEN_HEIGHT + LOWER_MARGIN - 90)
    draw_text('Press UP or DOWN to change the level', font, RED, 10, SCREEN_HEIGHT + LOWER_MARGIN - 60)
    
    if save_button.draw(screen):
        #saves the data of that level
        with open(f'level{level}_data.csv', 'w', newline='') as csvfile: #w means for writing so we're gonna be able to wrtie to it
            writer = csv.writer(csvfile, delimiter = ',') #the delimiter separates each of the values
            for row in world_data:
                writer.writerow(row)

    if load_button.draw(screen):
        #loads the data of a certain level
        scroll = 0
        with open(f'level{level}_data.csv', newline='') as csvfile: 
            reader = csv.reader(csvfile, delimiter = ',') 
            for x, row in enumerate(reader):
                for y, tile in enumerate(row):
                    world_data[x][y] = int(tile)


    #draw tile panel and tiles
    pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH, 0, SIDE_MARGIN, SCREEN_HEIGHT))

    #choose a tile
    button_count = 0
    for button_count, i in enumerate(button_list):
        if i.draw(screen):
            current_tile = button_count
    
    #highlights the selected tile
    pygame.draw.rect(screen, RED, button_list[current_tile].rect, 3)

    

    #scrolling
    if scroll_left == True and scroll > 0:
        scroll -= 5 * scroll_speed #in px
    if scroll_right == True and scroll < (MAXIMUM_COLUMNS * TILE_SIZE) - SCREEN_WIDTH:
        scroll += 5 * scroll_speed

    #add new tiles to the screen
    #get mouse position
    pos = pygame.mouse.get_pos()
    x = (pos[0] + scroll) // TILE_SIZE
    y = pos[1] // TILE_SIZE


    #check that the coords are within the tile area
    if pos[0] < SCREEN_WIDTH and pos[1] < SCREEN_HEIGHT:
        #update tile value
        if pygame.mouse.get_pressed()[0] == 1:
            if world_data[y][x] != current_tile:
                world_data[y][x] = current_tile
        if pygame.mouse.get_pressed()[2] == 1: #right click to delete
            world_data[y][x] = -1   

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        #keyboard presses
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                level += 1
            if event.key == pygame.K_DOWN and level > 0:
                level -= 1
            if event.key == pygame.K_LEFT:
                scroll_left = True
            if event.key == pygame.K_RIGHT:
                scroll_right = True
            if event.key == pygame.K_RSHIFT:
                scroll_speed = 5
            if event.key == pygame.K_ESCAPE:
                run = False

        #keyboard releases
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                scroll_left = False
            if event.key == pygame.K_RIGHT:
                scroll_right = False
            if event.key == pygame.K_RSHIFT:
                scroll_speed = 1


        

    pygame.display.update()

pygame.quit()