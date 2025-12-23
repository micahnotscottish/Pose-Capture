from ultralytics import YOLO
from config import YOLO_MODEL_PATH
import pygame
from game.cam_configuration import Configuration
from game.draw_character import CharacterDraw
from game.meteor_game import MeteorGame

# This is the main class that controls the motion capture game.
# From here, the main game loop calls the camera configuration,
# the character drawing (which handles motion capture on its own),
# and additional game functionality.

class myGame:    
    def __init__(self):
        self.win_w = 1920
        self.win_h = 1080
        self.mirror = True
        self.spawn_timer = 0
        self.model = YOLO(YOLO_MODEL_PATH)
        pygame.init()
        self.screen = pygame.display.set_mode((self.win_w, self.win_h), pygame.RESIZABLE)
        pygame.display.set_caption("Motion Capture Dinosuar Game")
        self.clock = pygame.time.Clock()

        # preload all character sprites
        # this dicionary can easily be changed to any sprites wanted
        # without hindering the character drawing process
        self.background_image = pygame.image.load("sprites/background.png").convert_alpha()
        sprite_paths = {
            "head": "sprites/head.png",
            "left_forearm": "sprites/arm.png",
            "right_forearm": "sprites/arm.png",
            "left_bicep": "sprites/bicep.png",
            "right_bicep": "sprites/bicep.png",
            "torso": "sprites/torso.png",
            "left_thigh": "sprites/thigh.png",
            "right_thigh": "sprites/thigh.png",
            "left_shin": "sprites/shin.png",
            "right_shin": "sprites/shin.png",
        }
        self.sprites = {}
        for name, path in sprite_paths.items():
            sprite = pygame.image.load(path).convert_alpha()
            self.sprites[name] = sprite


        # configure camera
        self.displayConf = Configuration(self.screen, initial_scale=1.0, initial_offx=0, initial_offy=0)
        self.user_scale, self.user_offx, self.user_offy, self.crop_left, self.crop_right = self.displayConf.configuration()
                
        # configure chracter drawing and motion capture (uses variables returned from camera configuration to adjust image)
        self.draw_character = CharacterDraw(self.screen, self.model, self.user_offx, self.user_offy, self.user_scale, self.crop_left, self.crop_right, self.mirror, self.sprites)
        
        # configure the game to be played
        # this can easily be swapped out for any other game without effecting the motion capture or character
        self.game = MeteorGame()
        
    
    def run_pygame_loop(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.screen.fill((0, 255, 0))
            self.screen.blit(self.background_image, (0, 0))
            
            # draw character and get hitbox wanted for this game
            self.draw_character.draw_character()
            hitbox = self.draw_character.get_head_rect()
                    
            # this particular game can spawn meteors,
            # so setup a time to spawn them
            self.spawn_timer += 1
            if self.spawn_timer >= 40:
                self.game.spawn_meteor(self.screen.get_width())
                self.spawn_timer = 0

            # this particular game requires updating and drawing meteors every frame
            self.game.update_and_draw_meteors(self.screen, hitbox)

            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()
        



