import cv2
from ultralytics import YOLO
from config import YOLO_MODEL_PATH
import flask_app
import pygame
import numpy as np


def run_pygame_loop():
        win_w = 1920
        win_h = 1080
        img_x = 0
        img_y = 0
        max_w = win_w 
        max_h = 1080
        mirror = True

        model = YOLO(YOLO_MODEL_PATH)

        pygame.init()
        screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
        pygame.display.set_caption("YOLOv8 Pose - All Keypoints")
        clock = pygame.time.Clock()

        

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

            # Scale image to fit width
            h, w = frame.shape[:2]
            scale = win_w / w
            disp_w = win_w
            disp_h = max(1, int(round(h * scale)))

            # Compute top-left corner to center vertically
            img_x = 0
            img_y = max(0, (win_h - disp_h) // 2)

            # Resize frame
            resized = cv2.resize(frame, (disp_w, disp_h))
            if mirror:
                resized = cv2.flip(resized, 1)


            # Run pose detection on resized image so keypoints match display coords
            results = model(resized, verbose=False)

            # Convert to RGB for pygame
            frame_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

            # Create surface from buffer (size = (width, height))
            frame_surface = pygame.image.frombuffer(frame_rgb.tobytes(), (disp_w, disp_h), 'RGB')

            # Optional: clear background (fill with black)
            screen.fill((0, 0, 0))

            # Blit image at requested position
            #screen.blit(frame_surface, (img_x, img_y))

            # Draw keypoints (offset by image position)
            if results and len(results) > 0 and getattr(results[0], 'keypoints', None) is not None:
                kpts = results[0].keypoints
                xy = kpts.xy.cpu().numpy()      # (people, num_kpts, 2)
                conf = kpts.conf.cpu().numpy()  # (people, num_kpts)

                if xy.size > 0:
                    person = xy[0]
                    person_conf = conf[0]

                    for i in range(person.shape[0]):
                        x, y = person[i]
                        c = person_conf[i]
                        if c > 0.5:
                            draw_x = img_x + int(round(x))
                            draw_y = img_y + int(round(y))
                            pygame.draw.circle(screen, (255, 0, 0), (draw_x, draw_y), 6)

            flask_app.processing = False
            pygame.display.flip()
            clock.tick(30)

        pygame.quit()
