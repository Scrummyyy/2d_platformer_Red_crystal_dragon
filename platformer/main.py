import pygame
from pygame.locals import *
from pygame import mixer
from os import path

pygame.mixer.pre_init(44100, - 16, 2, 512)
mixer.init()
pygame.init()

clock = pygame.time.Clock()
fps = 60

screen_width = 1000
screen_height = 1000

#Головний екран
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Platformer')

font = pygame.font.SysFont('Bauhaus 93', 70)
font_score = pygame.font.SysFont('Bauhaus 93', 30)


tile_size = 50
game_over = 0
main_menu = True
level = 1
max_levels = 7
score = 0
saved_score = 0

white = (255, 255, 255)
blue = (0, 0, 255)
red = (255, 0, 0)

#Завантаження зображень гри
bg_img = pygame.image.load(f'img/bg/{level}.png')
menu_img = pygame.image.load('img/menu.jpg')
restart_img = pygame.image.load('img/button-restart.jpg')
start_img = pygame.image.load('img/new_game-button.png')
exit_img = pygame.image.load('img/quit-button.png')
win_img = pygame.image.load('img/win.jpg')

#Завантаження музики
pygame.mixer.music.load('music/background.mp3')
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1, 0.0, 5000)
lose_fx = pygame.mixer.Sound('music/sorrow.mp3')
lose_fx.set_volume(0.5)
crystal_fx = pygame.mixer.Sound('music/crystal.mp3')
crystal_fx.set_volume(0.5)


def draw_grid():
    for line in range(0, 20):
        pygame.draw.line(screen, (255, 255, 255), (0, line * tile_size), (screen_width, line * tile_size))
        pygame.draw.line(screen, (255, 255, 255), ( line * tile_size, 0), ( line * tile_size,screen_height))

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))
def reset_level(level):
    player.reset(100, screen_height - 100)
    ghost_group.empty()
    platform_group.empty()
    lava_group.empty()
    crystal_group.empty()
    exit_group.empty()


    # Відкриття файлу для читання
    if path.exists(f'level0{level}.txt'):
        with open(f'level0{level}.txt', 'r') as file:
            # Построчно читаємо файл
            for line in file:
                # Розділяємо рядок на окремі числа, конвертуємо їх у цілі числа та додаємо до списку рівня
                world_data.append(list(map(int, line.strip().split(','))))
    # Створення світу
    world = World(world_data)
    return world



class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        action = False

        #Отримання координатів курсора миші
        pos = pygame.mouse.get_pos()

        #Перевірка натискання миші
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False


        screen.blit(self.image, self.rect)

        return action

class Player():
    def __init__(self, x, y):
        self.reset(x, y)
    def update(self, game_over):
        dx = 0
        dy = 0
        walk_cooldown = 5
        col_thresh = 20


        #Натискання клавіш
        if game_over == 0:
            key = pygame.key.get_pressed()
            if key[pygame.K_SPACE] and self.jumped == False and self.in_air == False:
                self.vel_y = -15
                self.jumped = True
            if key[pygame.K_SPACE] == False:
                self.jumped = False
            if key[pygame.K_LEFT]:
                dx -= 5
                self.counter += 1
                self.direction = -1
            if key[pygame.K_RIGHT]:
                dx += 5
                self.counter += 1
                self.direction = 1
            if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False:
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            #анімація
            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            #гравітація
            self.vel_y += 1
            if self.vel_y > 10:
               self.vel_y = 10
            dy += self.vel_y

            #Перевірка колізії
            self.in_air = True
            for tile in world.tile_list:
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0

                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False


            #Колізія для ворогів
            if pygame.sprite.spritecollide(self, ghost_group, False):
                lose_fx.play()
                game_over = -1
            if pygame.sprite.spritecollide(self, lava_group, False):
                lose_fx.play()
                game_over = -1

            if pygame.sprite.spritecollide(self, exit_group, False):
                game_over = 1

            #Колізія для платформи
            for platform in platform_group:
                # x
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # y
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    if abs((self.rect.top + dy) - platform.rect.bottom) < col_thresh:
                        self.vel_y = 0
                        dy = platform.rect.bottom - self.rect.top
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < col_thresh:
                        self.rect.bottom = platform.rect.top - 1
                        self.in_air = False
                        dy = 0

                    if platform.move_x != 0:
                        self.rect.x += platform.move_direction

            self.rect.x += dx
            self.rect.y += dy

        elif game_over == -1:
            self.image = self.dead_image




        screen.blit(self.image, self.rect)
        #pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)
        return game_over

    def reset(self, x, y):
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        for num in range(1, 11):
            img_right = pygame.image.load(f'img/sprite/sprite{num}.png')
            img_right = pygame.transform.scale(img_right, (57, 70))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)
        self.dead_image = pygame.image.load('img/dead.png')
        self.dead_image = pygame.transform.scale(self.dead_image, (57, 70))
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air = True

class World():
    def __init__(self, data):
        self.tile_list = []
#Завантаження зображень платформи
        dirt_img = pygame.image.load('img/dirt-platform.png')
        mod_img = pygame.image.load('img/dirty-2.png')
        rock_img = pygame.image.load('img/platform.jpg')
        wood_img = pygame.image.load('img/wood-platform.jpg')
        neon_img = pygame.image.load('img/neon_platform.jpg')
        grass_img = pygame.image.load('img/grass-platform.jpg')
        lava_img = pygame.image.load('img/lava.jpg')
        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(dirt_img,(tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 2:
                    img = pygame.transform.scale(mod_img,(tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 3:
                    ghost = Enemy(col_count * tile_size + 10, row_count * tile_size - 10)
                    ghost_group.add(ghost)
                if tile == 4:
                    img = pygame.transform.scale(rock_img,(tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 5:
                    img = pygame.transform.scale(wood_img,(tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 6:
                    lava = Lava(col_count * tile_size, row_count * tile_size + tile_size // 2)
                    lava_group.add(lava)
                if tile == 7:
                    crystal = Crystal(col_count * tile_size + tile_size // 2, row_count * tile_size + tile_size // 2)
                    crystal_group.add(crystal)
                if tile == 8:
                    exit = Exit(col_count * tile_size - 20, row_count * tile_size - 20)
                    exit_group.add(exit)
                if tile == 9:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1)
                    platform_group.add(platform)
                if tile == 10:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0)
                    platform_group.add(platform)
                if tile == 13:
                    img = pygame.transform.scale(neon_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 14:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 15:
                    img = pygame.transform.scale(lava_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                col_count += 1
            row_count += 1
    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])
            #pygame.draw.rect(screen,(255, 255, 255), tile[1], 2)
#
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('img/sprite-enemy/enemy.png')
        self.image = pygame.transform.scale(self.image, (34, 54))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) >= 50:
            self.move_direction *= -1
            self.move_counter *= -1

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, move_x, move_y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/movie.jpg')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_counter = 0
        self.move_direction = 1
        self.move_x = move_x
        self.move_y = move_y

    def update(self):
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1
class Lava(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/lava/lava.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Crystal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img= pygame.image.load('img/crystal.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img= pygame.image.load('img/exit.png')
        self.image = pygame.transform.scale(img, (1.5 * tile_size, 1.5 * tile_size))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


player = Player(100, screen_height - 150)

ghost_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
crystal_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

#score_crystal = Crystal(tile_size // 2, tile_size // 2)
#crystal_group.add(score_crystal)

#Завантаження рівнів гри
world_data = []

# Відкриття файлу для читання
if path.exists(f'level0{level}.txt'):
    with open(f'level0{level}.txt', 'r') as file:
        # Построчно читаємо файл
        for line in file:
            # Розділяємо рядок на окремі числа, конвертуємо їх у цілі числа та додаємо до списку рівня
            world_data.append(list(map(int, line.strip().split(','))))

# Створення світу
world = World(world_data)

menu_img = pygame.transform.scale(menu_img, (screen_width, screen_height + 150))
#створюємо кнопки
restart_button = Button(screen_width // 2 - 50, screen_height // 2 + 50, restart_img)
start_button = Button(screen_width // 2 - 350, screen_height // 2, start_img)
exit_button = Button(screen_width // 2 + 150, screen_height // 2, exit_img)



run = True
while run:
    clock.tick(fps)
    if main_menu == True:
        screen.blit(menu_img, (0, -150))
        if exit_button.draw():
            run = False
        if start_button.draw():
            level = 1
            main_menu = False
    else:
        # Вивантаження зображення на головний екран
        if level == 1:
            screen.blit(bg_img, (-650, 0))
        elif level == 3:
            screen.blit(bg_img, (-500, 0))
        elif level == 4:
            screen.blit(pygame.transform.scale(bg_img, (screen_width, screen_height)), (0, 0))
        elif level == 5:
            screen.blit(pygame.transform.scale(bg_img, (screen_width, screen_height)), (0, 0))
        elif level == 6:
            screen.blit(bg_img, (-500, 0))
        elif level == 7:
            screen.blit(bg_img, (-500, 0))
        else:
            screen.blit(bg_img, (0, 0))
        world.draw()

        if game_over == 0:
            ghost_group.update()
            platform_group.update()
            #оновлення рахунку гри
            if pygame.sprite.spritecollide(player, crystal_group, True):
                crystal_fx.play()
                score += 1

        crystal_group.draw(screen)
        ghost_group.draw(screen)
        platform_group.draw(screen)
        lava_group.draw(screen)
        exit_group.draw(screen)
        game_over = player.update(game_over)

        if game_over == -1:
            draw_text('GAME OVER!', font, red, screen_width // 2 - 140, screen_height // 2 - 100)
            draw_text('Your score:' + str(score) + '/37', font, red, screen_width // 2 - 180, screen_height // 2 - 40)
            if restart_button.draw():
                world_data = []
                world = reset_level(level)
                score = saved_score
                print(score)
                game_over = 0


        #Гравець пройшов рівень гри
        if game_over == 1:
            level += 1
            if level <= max_levels:
                bg_img = pygame.image.load(f'img/bg/{level}.png')
                world_data = []
                world = reset_level(level)
                game_over = 0
                saved_score = score
            else:
                screen.blit(pygame.transform.scale(win_img, (screen_width, screen_height)), (0, 0))
                draw_text('YOU WIN!', font, blue, screen_width // 2 - 140, screen_height // 2 - 100)
                draw_text('Your score:' + str(score) + '/37', font, blue, screen_width // 2 - 140, screen_height // 2 - 40)
                if restart_button.draw():
                   level = 1
                   world_data = []
                   world = reset_level(level)
                   game_over = 0
                   bg_img = pygame.image.load(f'img/bg/1.png')
                   main_menu = True
    #Вихід з гри
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()
