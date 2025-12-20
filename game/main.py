import cv2
from ultralytics import YOLO
from config import YOLO_MODEL_PATH
import flask_app
import pygame
import numpy as np
from game import draw_character, draw_meteors, cam_configuration
from game.cam_configuration import Configuration

class myGame:
    
    def __init__(self):
        pass
        
    
    def run_pygame_loop(self):
        
        win_w = 1920
        win_h = 1200
        img_x = 0
        img_y = 0
        max_w = win_w 
        max_h = 1080
        mirror = True
        spawn_timer = 0
        # smoothing parameters
        smoothing_alpha = 1  # higher = follow new positions more closely
        conf_threshold = 0.5
        smoothed_person = None
        smoothed_people = None
        
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

        # Attempt to get a sample frame for configuration
        sample_frame = None
        if flask_app.latest_frame is not None:
            try:
                sample_frame = flask_app.latest_frame.copy()
            except Exception:
                sample_frame = None

        # Show configuration UI and get scale/offsets
        displayConf = Configuration(screen, sample_frame, initial_scale=1.0, initial_offx=0, initial_offy=0)
        user_scale, user_offx, user_offy = displayConf.configuration()
        
        
        
        # --------- MAIN GAME LOOP -----------
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            frame = None
            if flask_app.latest_frame is not None and not flask_app.processing:
                flask_app.processing = True
                frame = flask_app.latest_frame.copy()
                flask_app.latest_frame = None

            if frame is None:
                # Nothing new, continue rendering (could draw UI behind image)
                pygame.display.flip()
                clock.tick(30)
                continue

            # Get current window size (if user resized)
            win_w, win_h = screen.get_size()

            # Use user-controlled uniform scale and offsets
            h, w = frame.shape[:2]
            disp_w = max(1, int(round(w * user_scale)))
            disp_h = max(1, int(round(h * user_scale)))

            # Compute centered position and apply offsets
            img_x = (win_w - disp_w) // 2 + user_offx
            img_y = (win_h - disp_h) // 2 + user_offy

            # Resize frame according to user scale
            resized = cv2.resize(frame, (disp_w, disp_h))
            if mirror:
                resized = cv2.flip(resized, 1)


            # Run pose detection on resized image so keypoints match display coords
            results = model(resized, verbose=False)

            # Optional: clear background (fill with black)
            screen.fill((0, 255, 0))

            # Blit image at requested position
            #screen.blit(frame_surface, (img_x, img_y))
            screen.blit(background_image, (0, 0))

            # Draw keypoints (offset by image position)
            if results and len(results) > 0 and getattr(results[0], 'keypoints', None) is not None:
                kpts = results[0].keypoints
                xy = kpts.xy.cpu().numpy()      # (people, num_kpts, 2)
                conf = kpts.conf.cpu().numpy()  # (people, num_kpts)

                num_people = xy.shape[0]

                # Initialize smoothing storage ONCE
                if smoothed_people is None:
                    smoothed_people = []

                # Ensure buffer count matches detected people
                while len(smoothed_people) < num_people:
                    smoothed_people.append(xy[len(smoothed_people)].copy())

                if len(smoothed_people) > num_people:
                    smoothed_people = smoothed_people[:num_people]

                # Draw each detected person
                for p in range(num_people):
                    person = xy[p]
                    person_conf = conf[p]
                    smoothed_person = smoothed_people[p]

                    # Exponential smoothing per keypoint with fallback for missing points.
                    # Keep a copy of the previous smoothed positions so we can compute
                    # the average translation of detected keypoints and apply that
                    # translation to any undetected keypoints so they move with the body.
                    prev_smoothed = smoothed_person.copy()
                    detected_idxs = []

                    for i in range(person.shape[0]):
                        if person_conf[i] >= conf_threshold:
                            smoothed_person[i] = (
                                smoothing_alpha * person[i]
                                + (1.0 - smoothing_alpha) * prev_smoothed[i]
                            )
                            detected_idxs.append(i)

                    # If at least one keypoint was detected, compute average translation
                    # and apply it to undetected keypoints so they follow the motion.
                    if len(detected_idxs) > 0:
                        deltas = smoothed_person[detected_idxs] - prev_smoothed[detected_idxs]
                        avg_delta = np.mean(deltas, axis=0)
                        for i in range(person.shape[0]):
                            if person_conf[i] < conf_threshold:
                                smoothed_person[i] = prev_smoothed[i] + avg_delta

                    # Draw this character
                    draw_character.draw_character(
                        screen,
                        img_x,
                        img_y,
                        smoothed_person,
                        person_conf,
                        sprites
                    )
                    
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
        



