import cv2
from ultralytics import YOLO
from config import YOLO_MODEL_PATH
import flask_app
import pygame
import numpy as np
from game import draw_character, draw_meteors


def _draw_slider(surface, rect, t, label):
    # rect: (x,y,w,h), t: 0..1
    x, y, w, h = rect
    pygame.draw.rect(surface, (50, 50, 50), rect)
    inner = (x + 4, y + 4, w - 8, h - 8)
    pygame.draw.rect(surface, (80, 80, 80), inner)
    knob_x = int(x + 4 + (w - 8) * t)
    knob_rect = (knob_x - 6, y + h // 2 - 8, 12, 16)
    pygame.draw.rect(surface, (200, 200, 200), knob_rect)
    font = pygame.font.SysFont(None, 20)
    txt = font.render(f"{label}: {t:.2f}", True, (255, 255, 255))
    surface.blit(txt, (x, y - 22))


def configuration(screen, sample_bgr, initial_scale=1.0, initial_offx=0, initial_offy=0):
    """Show sliders to configure scale and offsets. Returns (scale, offx, offy).

    sample_bgr: OpenCV BGR image to preview.
    """
    clock = pygame.time.Clock()
    win_w, win_h = screen.get_size()

    # preview surface will be updated each loop from a live frame if available
    preview_surf = None
    ph, pw = 0, 0

    # slider state: t in 0..1 maps to scale SCALE_MIN..SCALE_MAX, offx/offy -range..range
    SCALE_MIN = 0.2
    SCALE_MAX = 3.0
    t_scale = max(0.0, min(1.0, (initial_scale - SCALE_MIN) / (SCALE_MAX - SCALE_MIN)))
    max_offx = win_w // 2
    max_offy = win_h // 2
    t_offx = (initial_offx + max_offx) / (2 * max_offx) if max_offx else 0.5
    t_offy = (initial_offy + max_offy) / (2 * max_offy) if max_offy else 0.5

    dragging = None
    running = True
    font = pygame.font.SysFont(None, 28)

    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return initial_scale, initial_offx, initial_offy
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos
                # slider areas
                s1 = (50, win_h - 200, win_w - 100, 24)
                s2 = (50, win_h - 160, win_w - 100, 24)
                s3 = (50, win_h - 120, win_w - 100, 24)
                if pygame.Rect(*s1).collidepoint(mx, my):
                    dragging = ('scale', s1)
                elif pygame.Rect(*s2).collidepoint(mx, my):
                    dragging = ('offx', s2)
                elif pygame.Rect(*s3).collidepoint(mx, my):
                    dragging = ('offy', s3)
                else:
                    # configure button
                    cfg_rect = pygame.Rect(win_w // 2 - 80, win_h - 70, 160, 40)
                    if cfg_rect.collidepoint(mx, my):
                        # Map t values to real
                        scale = SCALE_MIN + t_scale * (SCALE_MAX - SCALE_MIN)
                        offx = int(round(t_offx * 2 * max_offx - max_offx))
                        offy = int(round(t_offy * 2 * max_offy - max_offy))
                        return scale, offx, offy
            elif ev.type == pygame.MOUSEBUTTONUP:
                dragging = None
            elif ev.type == pygame.MOUSEMOTION and dragging is not None:
                _, rect = dragging
                rx, ry, rw, rh = rect
                mx = ev.pos[0]
                t = (mx - rx) / float(max(1, rw))
                t = max(0.0, min(1.0, t))
                if dragging[0] == 'scale':
                    t_scale = t
                elif dragging[0] == 'offx':
                    t_offx = t
                elif dragging[0] == 'offy':
                    t_offy = t

        # update preview from latest live frame if available
        live = None
        try:
            if flask_app.latest_frame is not None:
                live = flask_app.latest_frame.copy()
        except Exception:
            live = None

        if live is not None:
            try:
                preview = cv2.cvtColor(live, cv2.COLOR_BGR2RGB)
                ph, pw = preview.shape[:2]
                preview_surf = pygame.image.frombuffer(preview.tobytes(), (pw, ph), 'RGB')
            except Exception:
                preview_surf = None

        # draw UI
        screen.fill((30, 30, 30))
        # preview centered (if available) and transformed live according to sliders
        if preview_surf is not None and pw > 0 and ph > 0:
            # map t_scale to real scale
            scale_val = SCALE_MIN + t_scale * (SCALE_MAX - SCALE_MIN)

            # compute a base fit scale so the preview fits comfortably in the UI
            max_preview_w = int(win_w * 0.8)
            max_preview_h = int(win_h * 0.6)
            base_fit = min(max_preview_w / float(pw), max_preview_h / float(ph))

            final_w = max(1, int(round(pw * base_fit * scale_val)))
            final_h = max(1, int(round(ph * base_fit * scale_val)))

            scaled = pygame.transform.smoothscale(preview_surf, (final_w, final_h))

            # compute offsets in pixels from t_offx/t_offy
            max_offx_preview = win_w // 2
            max_offy_preview = win_h // 2
            offx_px = int(round(t_offx * 2 * max_offx_preview - max_offx_preview))
            offy_px = int(round(t_offy * 2 * max_offy_preview - max_offy_preview))

            pv_x = (win_w // 2 - final_w // 2) + offx_px
            pv_y = (win_h // 2 - final_h // 2 - 60) + offy_px
            screen.blit(scaled, (pv_x, pv_y))
        else:
            # placeholder box
            placeholder = pygame.Rect(win_w // 2 - 320, win_h // 2 - 240 - 60, 640, 480)
            pygame.draw.rect(screen, (50, 50, 50), placeholder)
            no_txt = pygame.font.SysFont(None, 24).render('Waiting for camera...', True, (200, 200, 200))
            screen.blit(no_txt, (placeholder.x + 12, placeholder.y + 12))

        s1 = (50, win_h - 200, win_w - 100, 24)
        s2 = (50, win_h - 160, win_w - 100, 24)
        s3 = (50, win_h - 120, win_w - 100, 24)
        _draw_slider(screen, s1, t_scale, 'Scale')
        _draw_slider(screen, s2, t_offx, 'Offset X')
        _draw_slider(screen, s3, t_offy, 'Offset Y')

        # Configure button
        cfg_rect = pygame.Rect(win_w // 2 - 80, win_h - 70, 160, 40)
        pygame.draw.rect(screen, (70, 140, 70), cfg_rect)
        txt = font.render('Configure', True, (255, 255, 255))
        txt_rect = txt.get_rect(center=cfg_rect.center)
        screen.blit(txt, txt_rect)

        pygame.display.flip()
        clock.tick(30)




def run_pygame_loop():
        
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
        user_scale, user_offx, user_offy = configuration(screen, sample_frame, initial_scale=1.0, initial_offx=0, initial_offy=0)
        
        
        
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
        



