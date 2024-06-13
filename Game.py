import os
import sys
import math
import random
import pygame
from Scripts.utils import load_image, load_images, Animation
from Scripts.entities import PhysicsEntity, Player, Enemy
from Scripts.tilemap import Tilemap
from Scripts.clouds import Clouds
from Scripts.particle import Particle
from Scripts.spark import Spark
from Scripts.pyvidplayer import Video  # Ensure you have this module

#Pause menu assets
WHITE = (255, 255, 255, 128)
BLACK = (0, 0, 0)
BUTTON_COLOR = (0, 200, 0)
BUTTON_HOVER_COLOR = (0, 255, 0)
BUTTON_TEXT_COLOR = (255, 255, 255)
resume_button = pygame.Surface((200, 50))
quit_button = pygame.Surface((200, 50))
resume_button.fill(BUTTON_COLOR)
quit_button.fill(BUTTON_COLOR)

pygame.init()
pygame.display.set_caption('Deadline Dash')
screen = pygame.display.set_mode((1366, 768))
resume_button_img = pygame.image.load('data/images/resumebutton.png').convert_alpha()
quit_button_img = pygame.image.load('data/images/quitbutton.png').convert_alpha()
clock = pygame.time.Clock()

resume_button_img = pygame.transform.scale(resume_button_img, (200, 100))
quit_button_img = pygame.transform.scale(quit_button_img, (200, 100))

def draw_text(text, font, color, surface, x, y):
        textobj = font.render(text, True, color)
        textrect = textobj.get_rect()
        textrect.topleft = (x, y)
        surface.blit(textobj, textrect)


class Game:
    def __init__(self):
        
        self.pause_button_img = pygame.image.load('data/images/pausebutton.png').convert_alpha()
        self.pause_button_img = pygame.transform.scale(self.pause_button_img, (70, 70))
        self.pause_button_rect = self.pause_button_img.get_rect(topleft=(20, 10))

        
        
        self.screen = screen
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()
        
        self.movement = [False, False]

         # Initialize elapsed_time and timer_duration
        self.elapsed_time = 0
        self.timer_duration = 1800 #Example: 1800 frames = 30 seconds at 60 FPS

        # Initialize the font
        self.font = pygame.font.SysFont(None, 55)
        
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'background': load_image('background.png'),
            'clouds': load_images('clouds'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'gun': load_image('gun.png'),
            'projectile': load_image('projectile.png'),
        }
        
        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
        }
        
        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.7)
        
        self.clouds = Clouds(self.assets['clouds'], count=16)
        
        self.player = Player(self, (50, 50), (8, 15))
        
        self.tilemap = Tilemap(self, tile_size=16)
        
        self.level = 0
        self.load_level(self.level)
        
        self.screenshake = 0

        self.vid = Video('data/group7intro.mp4')
        self.vid.set_size((1366, 768))

    def pause_menu(self, screen, clock):
        paused = True
        font = pygame.font.SysFont(None, 55)

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 20)) 

        resume_button_img = pygame.transform.scale(pygame.image.load('data/images/resumebutton.png').convert_alpha(), (200, 100))
        quit_button_img = pygame.transform.scale(pygame.image.load('data/images/quitbutton.png').convert_alpha(), (200, 100))
        resume_button_rect = resume_button_img.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 50))
        quit_button_rect = quit_button_img.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 50))

        while paused:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        paused = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if resume_button_rect.collidepoint(mouse_pos):
                        paused = False
                    if quit_button_rect.collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()

            screen.blit(overlay, (0, 0))

            # Draw buttons
            screen.blit(resume_button_img, resume_button_rect.topleft)
            screen.blit(quit_button_img, quit_button_rect.topleft)

            pygame.display.update()
            clock.tick(60)
        
    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')
        
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))
            
        self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 3
            else:
                # Adjust the y-coordinate to ensure enemies spawn on top of the ground
                enemy_y = spawner['pos'][1] - 500  # Adjust this value according to your enemy's height
                self.enemies.append(Enemy(self, (spawner['pos'][0], enemy_y), (8, 15)))
            
        self.projectiles = []
        self.particles = []
        self.sparks = []
        
        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30

    def play_intro_video(self):
        self.vid.restart()  # Ensure the video starts from the beginning
        while self.vid.active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    self.vid.active = False

            self.screen.fill((0, 0, 0))
            self.vid.draw(self.screen, (0, 0))
            pygame.display.update()
            self.clock.tick(60)
        self.vid.close()
    
    
        
    def run(self, clock):
        self.play_intro_video()  # Play the video once at the start

        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
        
        self.sfx['ambience'].play(-1)
        
        while True:
            self.display.fill((0, 0, 0, 0))
            self.display_2.blit(self.assets['background'], (0, 0))
            
            self.screenshake = max(0, self.screenshake - 1)

            self.elapsed_time += 1

            if self.elapsed_time >= self.timer_duration:
                  self.dead = 1

            self.render_timer()
            
            if not len(self.enemies):
                self.transition += 1
                if self.transition > 30:
                    self.level = min(self.level + 1, len(os.listdir('data/maps')) - 1)
                    self.load_level(self.level)
            if self.transition < 0:
                self.transition += 1
            
            if self.dead:
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    self.load_level(self.level)
            
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] = (self.player.rect().centery - self.display.get_height() / 2) - 40  # Adjust this value to move the camera higher up
            
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))
            
            self.clouds.update()
            self.clouds.render(self.display_2, offset=render_scroll)
            
            self.tilemap.render(self.display, offset=render_scroll)
            
            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)
            
            if not self.dead:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.display, offset=render_scroll)
            
            # [[x, y], direction, timer]
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                img = self.assets['projectile']
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for i in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing) < 50:
                    if self.player.rect().collidepoint(projectile[0]):
                        self.projectiles.remove(projectile)
                        self.dead += 1
                        self.sfx['hit'].play()
                        self.screenshake = max(16, self.screenshake)
                        for i in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                            self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                        
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)
                    
            display_mask = pygame.mask.from_surface(self.display)
            display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_sillhouette, offset)
            
            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                   pygame.quit()
                   sys.exit()
                if event.type == pygame.KEYDOWN:
                   if event.key == pygame.K_ESCAPE:
                      self.pause_menu(self.screen, self.clock)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT:
                       self.movement[1] = True
                    if event.key == pygame.K_UP:
                      if self.player.jump():
                         self.sfx['jump'].play()
                    if event.key == pygame.K_x:
                        self.player.dash()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                       self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
                       self.movement[1] = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.pause_button_rect.collidepoint(event.pos):
                      self.pause_menu(screen, clock)

            if self.transition:
             transition_surf = pygame.Surface(self.display.get_size())
             pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
             transition_surf.set_colorkey((255, 255, 255))
            self.display.blit(transition_surf, (0, 0))

            self.display_2.blit(self.display, (0, 0))
  
            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset)
            screen.blit(self.pause_button_img, self.pause_button_rect.topleft)
                 
            pygame.display.update()
            self.clock.tick(60)
    
    def render_timer(self):
    # Convert elapsed time to seconds
        seconds = (self.timer_duration - self.elapsed_time) // 60

    # Render timer text
        timer_text = f"Timer: {seconds} seconds"
        text_surface = self.font.render(timer_text, True, pygame.Color('white'))

    # Display the timer text at the top middle of the screen
        text_rect = text_surface.get_rect(center=(self.screen.get_width() // 2, 30))  # Adjusted y-coordinate to 30 for visibility
        self.screen.blit(text_surface, text_rect)

    

Game().run(clock)