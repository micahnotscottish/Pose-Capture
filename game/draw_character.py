import pygame
import numpy as np
import flask_app
import cv2

# This class deals with all of the motion capturing,
# armature generation, and character drawing.


class CharacterDraw():
    def __init__(self, screen, model, user_offx, user_offy, user_scale, crop_left, crop_right, mirror, sprites):
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
        self.smoothing_alpha = .5  # higher = follow new positions more closely
        self.person = None
        self.min_conf = .5
        self.user_offx = user_offx
        self.user_offy = user_offy
        self.user_scale = user_scale
        self.conf = None
        self.crop_left = crop_left
        self.crop_right = crop_right
        self.head_rect = None
        self.smoothed_people = []
        
        
    # get the armature pose from YOLO and draw the character
    def draw_character(self):
        
        # get pose will populate person with a person,
        # so if there is not a person skip this frame
        self.get_pose()
        if self.person is None:
            return

        # YOLO indexes points from 0-17
        # draw coresponding sprites from point 1 to point 2
        self.draw_from_to(self.sprites["left_forearm"], 7, 9)
        self.draw_from_to(self.sprites["right_forearm"], 8, 10)
        self.draw_from_to(self.sprites["left_bicep"], 5, 7)
        self.draw_from_to(self.sprites["right_bicep"], 6, 8)
        self.draw_from_to(self.sprites["left_thigh"], 11, 13)
        self.draw_from_to(self.sprites["right_thigh"], 12, 14)
        self.draw_from_to(self.sprites["left_shin"], 13, 15)
        self.draw_from_to(self.sprites["right_shin"], 14, 16)
        # head and torso are handled seperately since they aren't "from and to" drawings
        self.draw_head(self.sprites["head"])
        self.draw_torso(self.sprites["torso"])
        
        # FOR DEBUGGING:
        # draws a circle at every index that is detected
        #for i in (5, 6, 7, 8, 11, 12, 13, 14 ):
        #    x, y = self.person[i]
        #    c = self.person_conf[i]
        #    if c > 0.5:
        #        draw_x = self.img_x + int(round(x))
        #        draw_y = self.img_y + int(round(y))
        #        pygame.draw.circle(self.screen, (35, 111, 33), (draw_x, draw_y), 6)
        
    
    # get the frame from the camera and convert it into a motion capture pose and points
    def get_pose(self):
        
        # get frame from camera and make a copy of it to be processed
        # "processing" is a lock to prevent overwriting during copying due to threaded programs
        frame = None
        if flask_app.latest_frame is not None and not flask_app.processing:
            flask_app.processing = True
            frame = flask_app.latest_frame.copy()
            flask_app.latest_frame = None
            flask_app.processing = False
        if frame is None:
            return
        

        # get image shape and apply offsets from configuration
        win_w, win_h = self.screen.get_size()
        h, w = frame.shape[:2]
        self.disp_w = max(1, int(round(w * self.user_scale)))
        self.disp_h = max(1, int(round(h * self.user_scale)))
        self.img_x = (win_w - self.disp_w) // 2 + self.user_offx
        self.img_y = (win_h - self.disp_h) // 2 + self.user_offy
        resized = cv2.resize(frame, (self.disp_w, self.disp_h))
        if self.mirror:
            resized = cv2.flip(resized, 1)

        # run the image through YOLO pose detection
        results = self.model(resized, verbose=False)

        # if a person was detected and keypoints could be deteremined parse the results
        if results and len(results) > 0 and getattr(results[0], 'keypoints', None) is not None:
            kpts = results[0].keypoints
            xy = kpts.xy.cpu().numpy()
            conf = kpts.conf.cpu().numpy()
            num_people = xy.shape[0]
                

            # ensure buffer count matches detected people
            while len(self.smoothed_people) < num_people:
                self.smoothed_people.append(xy[len(self.smoothed_people)].copy())

            if len(self.smoothed_people) > num_people:
                self.smoothed_people = self.smoothed_people[:num_people]

            # process detected person from people (only draw the primary person detected)
            for p in range(num_people):
                self.person = xy[p]
                self.person_conf = conf[p]
                smoothed_person = self.smoothed_people[p]

                # make a copy for smoothing
                prev_smoothed = smoothed_person.copy()
                detected_idxs = []

                # for every index detected on the person, only save it if the confidence is high
                # save the smoothed version, which is the average of the previous frame and the new one
                for i in range(self.person.shape[0]):
                    if self.person_conf[i] >= self.conf_threshold:
                        smoothed_person[i] = (self.smoothing_alpha * self.person[i] + (1.0 - self.smoothing_alpha) * prev_smoothed[i])
                        detected_idxs.append(i)

   
                # update smoothing buffer
                self.smoothed_people[p] = smoothed_person

                # take the horizontal average of all the points
                if len(detected_idxs) > 0:
                    center_x = float(np.mean(smoothed_person[detected_idxs, 0]))
                else:
                    center_x = float(self.disp_w) / 2.0

                # translate the average points horizontal location in the capture window
                # to the equivalent percentage of the game screen
                desired_screen_center_x = int((center_x / float(self.disp_w)) * win_w)
                final_img_x = desired_screen_center_x - (self.disp_w // 2) + self.user_offx

                # set final image pos and current person for drawing
                self.img_x = final_img_x
                self.img_y = (win_h - self.disp_h) // 2 + self.user_offy
                self.person = smoothed_person
                self.person_conf = conf[p]

                # break so only primary person is drawn
                # this could be changed to draw multiple people
                # initially I had it configured to draw everyone on screen (hence people variables being used)
                # but I ran into issues of YOLO struggling to differentiate people/points
                # when they were close in proximity or overlapping
                break
            
            
    # draw sprite from point to other point
    # used for appendages (biceps, arms, thighs, and shins)
    def draw_from_to(self, sprite, p1, p2):

        x1, y1 = self.person[p1]
        x2, y2 = self.person[p2]
        c1 = self.person_conf[p1]
        c2 = self.person_conf[p2]

        # both points require confidence for the sprite to be drawn
        if c1 > 0.5 and c2 > 0.5:
            # get the angle between the 2 points
            dx = x2 - x1
            dy = y2 - y1
            length = max(1, np.hypot(dx, dy))
            angle = np.degrees(np.arctan2(dy, dx))

            # scale the sprite based on the distance between the 2 points
            sprite_w, sprite_h = sprite.get_size()
            scale_factor = length / sprite_w
            new_w = int(sprite_w * scale_factor)
            new_h = int(sprite_h * scale_factor)
            scaled_sprite = pygame.transform.scale(sprite, (new_w, new_h))

            # rotate sprite
            rotated_sprite = pygame.transform.rotate(scaled_sprite, -angle)

            # position the sprite between the 2 points to connect them
            rect = rotated_sprite.get_rect()
            rect.center = (self.img_x + int(round((x1 + x2) / 2)), self.img_y + int(round((y1 + y2) / 2)))
            self.screen.blit(rotated_sprite, rect.topleft)
            
            
    # draw torso
    # YOLO doesn't have a center of mass point
    # so I calculate the average points between shoulders and hips
    # and scale to cover them
    def draw_torso(self, sprite):

        # yolo indexes needed
        LH, RH = 11, 12
        LS, RS = 5, 6

        # get x and y values of indexes
        lh_x, lh_y = self.person[LH]
        rh_x, rh_y = self.person[RH]
        ls_x, ls_y = self.person[LS]
        rs_x, rs_y = self.person[RS]

        # get confidence values for shoulders and hips
        lh_c, rh_c = self.person_conf[LH], self.person_conf[RH]
        ls_c, rs_c = self.person_conf[LS], self.person_conf[RS]

        # require confidence for both shoulders and hips
        if lh_c > 0.5 and rh_c > 0.5 and ls_c > 0.5 and rs_c > 0.5:

            # widths between shoulders and hips
            hip_width = np.hypot(rh_x - lh_x, rh_y - lh_y)
            shoulder_width = np.hypot(rs_x - ls_x, rs_y - ls_y)

            # take the largest width, either hips or shoulders
            torso_width = max(1, int(max(hip_width, shoulder_width)))

            # take the midpoint between the shoulders and hips to use as top and bottom edge
            hip_mid_y = (lh_y + rh_y) / 2
            shoulder_mid_y = (ls_y + rs_y) / 2

            # ensure that torso is at least drawn a little bit even if the shoulders and hips are super close together
            torso_height = max(1, int(abs(hip_mid_y - shoulder_mid_y)))

            # scale sprite to shoulders and hips
            scaled_sprite = pygame.transform.scale(sprite, (torso_width, torso_height))

            # center the sprite between the average of the shoulders and hips
            center_x = self.img_x + int(round((lh_x + rh_x + ls_x + rs_x) / 4))
            center_y = self.img_y + int(round((hip_mid_y + shoulder_mid_y) / 2))
            rect = scaled_sprite.get_rect(center=(center_x, center_y))
            self.screen.blit(scaled_sprite, rect.topleft)

            
    # this gets the center of the head
    # it uses all the different head points avaiable and uses the average,
    # since i was running into issues where turning the head would make a point or two
    # disappear and then the head was not able to be drawn
    def get_head_center(self):
        # YOLO indexes
        NOSE = 0
        LEFT_EAR = 3
        RIGHT_EAR = 4
        LEFT_SHOULDER = 5
        RIGHT_SHOULDER = 6

        points = []

        # check for each point in the head. if it has confidence then it will be used in the average
        if self.person_conf[NOSE] > self.min_conf:
            points.append(self.person[NOSE])

        if self.person_conf[LEFT_EAR] > self.min_conf:
            points.append(self.person[LEFT_EAR])

        if self.person_conf[RIGHT_EAR] > self.min_conf:
            points.append(self.person[RIGHT_EAR])

        # if no points in the head are detected at all, use the shoulders and roughly estimate where the head should be above it
        if not points and self.person_conf[LEFT_SHOULDER] > self.min_conf and self.person_conf[RIGHT_SHOULDER] > self.min_conf:
            sx = (self.person[LEFT_SHOULDER][0] + self.person[RIGHT_SHOULDER][0]) / 2
            sy = (self.person[LEFT_SHOULDER][1] + self.person[RIGHT_SHOULDER][1]) / 2
            return sx, sy - 40  # vertical offset guess

        if not points:
            return None

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return sum(xs) / len(xs), sum(ys) / len(ys)



    # draw the head around the average center of head points
    def draw_head(self, head_sprite):
        center = self.get_head_center()
        if center is None:
            return

        cx, cy = center

        shoulder_width = self.get_shoulder_width()
        if shoulder_width is None:
            return  # don’t draw if we can’t size it properly

        # scale the head based on how far apart the shoulders are
        head_size = int(shoulder_width * 1.5)
        head_sprite_scaled = pygame.transform.smoothscale(head_sprite, (head_size, head_size))
        self.head_rect = head_sprite_scaled.get_rect()
        self.head_rect.center = (self.img_x + int(cx), self.img_y + int(cy))
        self.screen.blit(head_sprite_scaled, self.head_rect.topleft)



    # returns the head rectangle to be used as a hitbox by games
    def get_head_rect(self):
        return self.head_rect
    
    
    # if there is confidence in the shoulders get the width that the shoulders are apart
    # used for scaling the head to shoulder width without having to store all the other variables
    # and indexes required by a function like draw torso
    def get_shoulder_width(self):
        LEFT_SHOULDER = 5
        RIGHT_SHOULDER = 6

        if (
            self.person_conf[LEFT_SHOULDER] > self.min_conf and
            self.person_conf[RIGHT_SHOULDER] > self.min_conf
        ):
            x1, _ = self.person[LEFT_SHOULDER]
            x2, _ = self.person[RIGHT_SHOULDER]
            return abs(x2 - x1)

        return None
