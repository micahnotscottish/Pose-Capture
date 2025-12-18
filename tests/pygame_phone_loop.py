import cv2
from ultralytics import YOLO
from config import YOLO_MODEL_PATH
import flask_app
import pygame
import numpy as np


def run_pygame_loop(
        model_path: str = None,
        window_size: tuple = (1000, 1000),
        image_pos: tuple = (0, 0),
        image_max_size: tuple = (1920, 2000),
        mirror: bool = True,
    ):
        """Display frames from `flask_app.latest_frame` in a pygame window.

        Parameters:
        - model_path: path to YOLO model (defaults to `YOLO_MODEL_PATH`).
        - window_size: (width, height) of pygame window.
        - image_pos: (x, y) top-left position within window where the image should be placed.
        - image_max_size: maximum (width, height) reserved for the image; the frame will be
          scaled to fit this area while preserving aspect ratio.
        - mirror: if True, flip the image horizontally before running detection.

        Keypoints are drawn in the same coordinate space as the displayed (resized) image,
        and offset by `image_pos` so circles line up with the image location.
        """

        model_path = model_path or YOLO_MODEL_PATH
        model = YOLO(model_path)

        pygame.init()
        WIN_W, WIN_H = window_size
        screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)
        pygame.display.set_caption("YOLOv8 Pose - All Keypoints")
        clock = pygame.time.Clock()

        img_x, img_y = image_pos
        max_w, max_h = image_max_size

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

            # Compute scale to fit the image into image_max_size while preserving aspect ratio
            h, w = frame.shape[:2]
            scale = min(max_w / w, max_h / h)
            disp_w = max(1, int(round(w * scale)))
            disp_h = max(1, int(round(h * scale)))

            # Resize frame to display size
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
            screen.blit(frame_surface, (img_x, img_y))

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
