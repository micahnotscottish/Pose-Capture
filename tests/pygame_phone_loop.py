import cv2
from ultralytics import YOLO
from config import YOLO_MODEL_PATH
import flask_app
import pygame
import numpy as np



def run_pygame_loop():
        
        win_w = 1920
        win_h = 1200
        img_x = 0
        img_y = 0
        max_w = win_w 
        max_h = 1080
        mirror = True
        # smoothing parameters
        smoothing_alpha = 0.5  # higher = follow new positions more closely
        conf_threshold = 0.5
        smoothed_person = None
        smoothed_people = None
        
        model = YOLO(YOLO_MODEL_PATH)

        pygame.init()
        screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
        pygame.display.set_caption("YOLOv8 Pose - All Keypoints")
        clock = pygame.time.Clock()

        # Load sprite (do this once outside loop ideally)
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

                    # Exponential smoothing per keypoint
                    for i in range(person.shape[0]):
                        if person_conf[i] >= conf_threshold:
                            smoothed_person[i] = (
                                smoothing_alpha * person[i]
                                + (1.0 - smoothing_alpha) * smoothed_person[i]
                            )

                    # Draw this character
                    draw_character(
                        screen,
                        img_x,
                        img_y,
                        smoothed_person,
                        person_conf,
                        sprites
                    )

            flask_app.processing = False
            pygame.display.flip()
            clock.tick(30)

        pygame.quit()
        

def draw_character(screen, img_x, img_y, person, person_conf, sprites):
    
    # Draw sprite from left elbow to left wrist
    # YOLOv8 pose indices: left elbow = 7, left wrist = 9
    draw_from_to(screen, img_x, img_y, person, person_conf, sprites["left_forearm"], 7, 9)
    draw_from_to(screen, img_x, img_y, person, person_conf, sprites["right_forearm"], 8, 10)
    draw_from_to(screen, img_x, img_y, person, person_conf, sprites["left_bicep"], 5, 7)
    draw_from_to(screen, img_x, img_y, person, person_conf, sprites["right_bicep"], 6, 8)
    draw_from_to(screen, img_x, img_y, person, person_conf, sprites["left_thigh"], 11, 13)
    draw_from_to(screen, img_x, img_y, person, person_conf, sprites["right_thigh"], 12, 14)
    draw_from_to(screen, img_x, img_y, person, person_conf, sprites["left_shin"], 13, 15)
    draw_from_to(screen, img_x, img_y, person, person_conf, sprites["right_shin"], 14, 16)
    draw_from_to(screen, img_x, img_y, person, person_conf, sprites["head"], 3, 4)
    draw_torso(screen, img_x, img_y, person, person_conf, sprites["torso"])
    
    # Draw all keypoints as circles
    for i in range(person.shape[0]):
        x, y = person[i]
        c = person_conf[i]
        if c > 0.5:
            draw_x = img_x + int(round(x))
            draw_y = img_y + int(round(y))
            pygame.draw.circle(screen, (255, 0, 0), (draw_x, draw_y), 8)
    
        
        
        
def draw_from_to(screen, img_x, img_y, person, person_conf, sprite, p1, p2):

    x1, y1 = person[p1]
    x2, y2 = person[p2]
    c1 = person_conf[p1]
    c2 = person_conf[p2]

    if c1 > 0.5 and c2 > 0.5:
        # Vector between points
        dx = x2 - x1
        dy = y2 - y1
        length = max(1, np.hypot(dx, dy))
        angle = np.degrees(np.arctan2(dy, dx))

        # Scale sprite
        sprite_w, sprite_h = sprite.get_size()
        scale_factor = length / sprite_w
        new_w = int(sprite_w * scale_factor)
        new_h = int(sprite_h * scale_factor)
        scaled_sprite = pygame.transform.scale(sprite, (new_w, new_h))

        # Rotate sprite
        rotated_sprite = pygame.transform.rotate(scaled_sprite, -angle)

        # Position sprite: center between points
        rect = rotated_sprite.get_rect()
        rect.center = (img_x + int(round((x1 + x2) / 2)),
                       img_y + int(round((y1 + y2) / 2)))

        screen.blit(rotated_sprite, rect.topleft)
        
        
def draw_torso(screen, img_x, img_y, person, person_conf, sprite):

    # Extract keypoints and confidence
    lh_x, lh_y = person[11]
    rh_x, rh_y = person[12]
    ls_x, ls_y = person[5]
    rs_x, rs_y = person[6]
    
    lh_c, rh_c = person_conf[11], person_conf[12]
    ls_c, rs_c = person_conf[5], person_conf[6]

    # Only draw if all points have high confidence
    if lh_c > 0.5 and rh_c > 0.5 and ls_c > 0.5 and rs_c > 0.5:
        # Compute torso width as distance between hips
        torso_width = max(1, int(np.hypot(rh_x - lh_x, rh_y - lh_y)))
        
        # Compute torso height as average vertical distance hips → shoulders
        avg_hip_y = (lh_y + rh_y) / 2
        avg_shoulder_y = (ls_y + rs_y) / 2
        torso_height = max(1, int(avg_hip_y - avg_shoulder_y))
        if torso_height < 0:
            torso_height = -torso_height  # ensure positive
        
        # Scale sprite to match torso size
        scaled_sprite = pygame.transform.scale(sprite, (torso_width, torso_height))
        
        # Compute center position for blit
        torso_center_x = img_x + int(round((lh_x + rh_x) / 2))
        torso_center_y = img_y + int(round((avg_shoulder_y + avg_hip_y) / 2))
        
        rect = scaled_sprite.get_rect(center=(torso_center_x, torso_center_y))
        
        screen.blit(scaled_sprite, rect.topleft)
