import pygame
import numpy as np
import flask_app
import cv2

class CharacterDraw():
    def __init__(self, screen, model, user_offx, user_offy, user_scale, mirror, sprites):
        self.screen = screen
        self.model = model
        self.disp_w = None
        self.disp_h = None
        self.img_x = None
        self.img_y = None
        self.mirror = mirror
        self.sprites = sprites
        self.person = None
        self.person_conf = None
        self.conf_threshold = 0.5
        self.smoothing_alpha = 1  # higher = follow new positions more closely
        self.person = None
        self.smoothed_people = None
        self.min_conf = .5
        self.user_offx = user_offx
        self.user_offy = user_offy
        self.user_scale = user_scale
        self.conf = None
        
        
    
    def draw_character(self):
        
        self.get_pose()
        # Draw sprite from left elbow to left wrist
        # YOLOv8 pose indices: left elbow = 7, left wrist = 9
        self.draw_from_to(self.sprites["left_forearm"], 7, 9)
        self.draw_from_to(self.sprites["right_forearm"], 8, 10)
        self.draw_from_to(self.sprites["left_bicep"], 5, 7)
        self.draw_from_to(self.sprites["right_bicep"], 6, 8)
        self.draw_from_to(self.sprites["left_thigh"], 11, 13)
        self.draw_from_to(self.sprites["right_thigh"], 12, 14)
        self.draw_from_to(self.sprites["left_shin"], 13, 15)
        self.draw_from_to(self.sprites["right_shin"], 14, 16)
        self.draw_head(self.sprites["head"])
        self.draw_torso(self.sprites["torso"])
        
        """"
        # Draw all keypoints as circles
        for i in range(person.shape[0]):
            x, y = person[i]
            c = person_conf[i]
            if c > 0.5:
                draw_x = img_x + int(round(x))
                draw_y = img_y + int(round(y))
                pygame.draw.circle(screen, (255, 0, 0), (draw_x, draw_y), 8)
        """
        
    
    def get_pose(self):
        frame = None
        if flask_app.latest_frame is not None and not flask_app.processing:
            flask_app.processing = True
            frame = flask_app.latest_frame.copy()
            flask_app.latest_frame = None

        if frame is None:
            # Nothing new, continue rendering (could draw UI behind image)
            #pygame.display.flip()
            #clock.tick(30)
            return
        
        # Use user-controlled uniform scale and offsets
        win_w, win_h = self.screen.get_size()
        h, w = frame.shape[:2]
        self.disp_w = max(1, int(round(w * self.user_scale)))
        self.disp_h = max(1, int(round(h * self.user_scale)))

        # Compute centered position and apply offsets
        self.img_x = (win_w - self.disp_w) // 2 + self.user_offx
        self.img_y = (win_h - self.disp_h) // 2 + self.user_offy

        
        # Resize frame according to user scale
        resized = cv2.resize(frame, (self.disp_w, self.disp_h))
        if self.mirror:
            resized = cv2.flip(resized, 1)


        # Run pose detection on resized image so keypoints match display coords
        results = self.model(resized, verbose=False)

        

        # Draw keypoints (offset by image position)
        if results and len(results) > 0 and getattr(results[0], 'keypoints', None) is not None:
            kpts = results[0].keypoints
            xy = kpts.xy.cpu().numpy()      # (people, num_kpts, 2)
            conf = kpts.conf.cpu().numpy()  # (people, num_kpts)

            num_people = xy.shape[0]

            # Initialize smoothing storage ONCE
            if self.smoothed_people is None:
                self.smoothed_people = []

            # Ensure buffer count matches detected people
            while len(self.smoothed_people) < num_people:
                self.smoothed_people.append(xy[len(self.smoothed_people)].copy())

            if len(self.smoothed_people) > num_people:
                self.smoothed_people = self.smoothed_people[:num_people]

            # Draw each detected person
            for p in range(num_people):
                self.person = xy[p]
                self.person_conf = conf[p]
                smoothed_person = self.smoothed_people[p]

                # Exponential smoothing per keypoint with fallback for missing points.
                # Keep a copy of the previous smoothed positions so we can compute
                # the average translation of detected keypoints and apply that
                # translation to any undetected keypoints so they move with the body.
                prev_smoothed = smoothed_person.copy()
                detected_idxs = []

                for i in range(self.person.shape[0]):
                    if self.person_conf[i] >= self.conf_threshold:
                        smoothed_person[i] = (
                            self.smoothing_alpha * self.person[i]
                            + (1.0 - self.smoothing_alpha) * prev_smoothed[i]
                        )
                        detected_idxs.append(i)

                # If at least one keypoint was detected, compute average translation
                # and apply it to undetected keypoints so they follow the motion.
                if len(detected_idxs) > 0:
                    deltas = smoothed_person[detected_idxs] - prev_smoothed[detected_idxs]
                    avg_delta = np.mean(deltas, axis=0)
                    for i in range(self.person.shape[0]):
                        if self.person_conf[i] < self.conf_threshold:
                            smoothed_person[i] = prev_smoothed[i] + avg_delta
            
            
    def draw_from_to(self, sprite, p1, p2):

        x1, y1 = self.person[p1]
        x2, y2 = self.person[p2]
        c1 = self.person_conf[p1]
        c2 = self.person_conf[p2]

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
            rect.center = (self.img_x + int(round((x1 + x2) / 2)),
                        self.img_y + int(round((y1 + y2) / 2)))

            self.screen.blit(rotated_sprite, rect.topleft)
            
            
    def draw_torso(self, sprite):

        # Keypoints
        LH, RH = 11, 12
        LS, RS = 5, 6

        lh_x, lh_y = self.person[LH]
        rh_x, rh_y = self.person[RH]
        ls_x, ls_y = self.person[LS]
        rs_x, rs_y = self.person[RS]

        lh_c, rh_c = self.person_conf[LH], self.person_conf[RH]
        ls_c, rs_c = self.person_conf[LS], self.person_conf[RS]

        # Require all points
        if lh_c > 0.5 and rh_c > 0.5 and ls_c > 0.5 and rs_c > 0.5:

            # Widths
            hip_width = np.hypot(rh_x - lh_x, rh_y - lh_y)
            shoulder_width = np.hypot(rs_x - ls_x, rs_y - ls_y)

            torso_width = max(1, int(max(hip_width, shoulder_width)))

            # Vertical extents
            hip_mid_y = (lh_y + rh_y) / 2
            shoulder_mid_y = (ls_y + rs_y) / 2

            torso_height = max(1, int(abs(hip_mid_y - shoulder_mid_y)))

            # Scale sprite
            scaled_sprite = pygame.transform.scale(sprite, (torso_width, torso_height))

            # Center of torso box
            center_x = self.img_x + int(round((lh_x + rh_x + ls_x + rs_x) / 4))
            center_y = self.img_y + int(round((hip_mid_y + shoulder_mid_y) / 2))

            rect = scaled_sprite.get_rect(center=(center_x, center_y))
            self.screen.blit(scaled_sprite, rect.topleft)

            
    def get_head_center(self):
        NOSE = 0
        LEFT_EAR = 3
        RIGHT_EAR = 4
        LEFT_SHOULDER = 5
        RIGHT_SHOULDER = 6

        points = []

        if self.conf[NOSE] > self.min_conf:
            points.append(self.person[NOSE])

        if self.conf[LEFT_EAR] > self.min_conf:
            points.append(self.person[LEFT_EAR])

        if self.conf[RIGHT_EAR] > self.min_conf:
            points.append(self.person[RIGHT_EAR])

        # Fallback to shoulders (estimate head above them)
        if not points and self.conf[LEFT_SHOULDER] > self.min_conf and self.conf[RIGHT_SHOULDER] > self.min_conf:
            sx = (self.person[LEFT_SHOULDER][0] + self.person[RIGHT_SHOULDER][0]) / 2
            sy = (self.person[LEFT_SHOULDER][1] + self.person[RIGHT_SHOULDER][1]) / 2
            return sx, sy - 40  # vertical offset guess

        if not points:
            return None

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return sum(xs) / len(xs), sum(ys) / len(ys)



    def draw_head(self, head_sprite):
        #center = self.get_head_center()
        center = None
        if center is None:
            return

        cx, cy = center

        rect = head_sprite.get_rect()
        rect.center = (self.img_x + int(cx), self.img_y + int(cy))
        self.screen.blit(head_sprite, rect.topleft)
