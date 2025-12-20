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
        pass
        
    
    def run_pygame_loop(self):
        
        win_w = 1920
        win_h = 1200
        mirror = True
        spawn_timer = 0
  
        model = YOLO(YOLO_MODEL_PATH)

        pygame.init()
        screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
        pygame.display.set_caption("YOLOv8 Pose - All Keypoints")
        clock = pygame.time.Clock()

        # Load sprite (do this once outside loop ideally)
        qrcode = pygame.image.load("qrcode/qr.png")
        qr_rect = qrcode.get_rect(center=(win_w // 2, win_h // 2))
        screen.blit(qrcode, qr_rect)

        background_image = pygame.image.load("sprites/background.png").convert_alpha()
        sprite_paths = {
            "head": "sprites/head.png",
            "left_forearm": "sprites/limb.png",
            "right_forearm": "sprites/limb.png",
            "left_bicep": "sprites/limb.png",
            "right_bicep": "sprites/limb.png",
            "torso": "sprites/torso.png",
            "left_thigh": "sprites/limb.png",
            "right_thigh": "sprites/limb.png",
            "left_shin": "sprites/limb.png",
            "right_shin": "sprites/limb.png",
        }
        
        sprites = {}
        for name, path in sprite_paths.items():
            sprite = pygame.image.load(path).convert_alpha()  # preserve transparency
            sprites[name] = sprite


        # Show configuration UI and get scale/offsets
        displayConf = Configuration(screen, initial_scale=1.0, initial_offx=0, initial_offy=0)
        user_scale, user_offx, user_offy = displayConf.configuration()
                

        draw_character = CharacterDraw(screen, model, user_offx, user_offy, user_scale, mirror, sprites)
        
        
        # --------- MAIN GAME LOOP -----------
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False


            # Optional: clear background (fill with black)
            screen.fill((0, 255, 0))

            # Blit image at requested position
            #screen.blit(frame_surface, (img_x, img_y))
            screen.blit(background_image, (0, 0))
            
            
            draw_character.draw_character()
                    
            spawn_timer += 1
            if spawn_timer >= 20:
                draw_meteors.spawn_meteor(screen.get_width())
                spawn_timer = 0

            # Update and draw meteors
            draw_meteors.update_and_draw_meteors(screen)

            flask_app.processing = False
            pygame.display.flip()
            clock.tick(30)

        pygame.quit()
        



