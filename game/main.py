import cv2
from ultralytics import YOLO
from config import YOLO_MODEL_PATH
import flask_app
import pygame
import numpy as np
from game import draw_character, draw_meteors, cam_configuration
from game.cam_configuration import Configuration
from game.draw_character import CharacterDraw

class myGame:
    
    def __init__(self):
        self.win_w = 1920
        self.win_h = 1080
        self.mirror = True
        self.spawn_timer = 0
  
        self.model = YOLO(YOLO_MODEL_PATH)

        pygame.init()
        self.screen = pygame.display.set_mode((self.win_w, self.win_h), pygame.RESIZABLE)
        pygame.display.set_caption("YOLOv8 Pose - All Keypoints")
        self.clock = pygame.time.Clock()

        # Load sprite (do this once outside loop ideally)
        qrcode = pygame.image.load("qrcode/qr.png")
        qr_rect = qrcode.get_rect(center=(self.win_w // 2, self.win_h // 2))
        self.screen.blit(qrcode, qr_rect)

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
            sprite = pygame.image.load(path).convert_alpha()  # preserve transparency
            self.sprites[name] = sprite


        # Show configuration UI and get scale/offsets
        self.displayConf = Configuration(self.screen, initial_scale=1.0, initial_offx=0, initial_offy=0)
        self.user_scale, self.user_offx, self.user_offy, self.crop_left, self.crop_right = self.displayConf.configuration()
                

        self.draw_character = CharacterDraw(self.screen, self.model, self.user_offx, self.user_offy, self.user_scale, self.crop_left, self.crop_right, self.mirror, self.sprites)
        pass
        
    
    def run_pygame_loop(self):
        
        
        # --------- MAIN GAME LOOP -----------
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False


            # Optional: clear background (fill with black)
            self.screen.fill((0, 255, 0))

            # Blit image at requested position
            #screen.blit(frame_surface, (img_x, img_y))
            self.screen.blit(self.background_image, (0, 0))
            
            
            self.draw_character.draw_character()
            hitbox = self.draw_character.get_head_rect()
                    
            self.spawn_timer += 1
            if self.spawn_timer >= 20:
                draw_meteors.spawn_meteor(self.screen.get_width())
                self.spawn_timer = 0

            # Update and draw meteors
            draw_meteors.update_and_draw_meteors(self.screen, hitbox)

            flask_app.processing = False
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        



