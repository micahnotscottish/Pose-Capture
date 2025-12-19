import pygame
import numpy as np

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
    draw_head(screen, img_x, img_y, person, person_conf, sprites["head"])
    draw_torso(screen, img_x, img_y, person, person_conf, sprites["torso"])
    
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

    # Keypoints
    LH, RH = 11, 12
    LS, RS = 5, 6

    lh_x, lh_y = person[LH]
    rh_x, rh_y = person[RH]
    ls_x, ls_y = person[LS]
    rs_x, rs_y = person[RS]

    lh_c, rh_c = person_conf[LH], person_conf[RH]
    ls_c, rs_c = person_conf[LS], person_conf[RS]

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
        center_x = img_x + int(round((lh_x + rh_x + ls_x + rs_x) / 4))
        center_y = img_y + int(round((hip_mid_y + shoulder_mid_y) / 2))

        rect = scaled_sprite.get_rect(center=(center_x, center_y))
        screen.blit(scaled_sprite, rect.topleft)

        
def get_head_center(person, conf, min_conf=0.5):
    NOSE = 0
    LEFT_EAR = 3
    RIGHT_EAR = 4
    LEFT_SHOULDER = 5
    RIGHT_SHOULDER = 6

    points = []

    if conf[NOSE] > min_conf:
        points.append(person[NOSE])

    if conf[LEFT_EAR] > min_conf:
        points.append(person[LEFT_EAR])

    if conf[RIGHT_EAR] > min_conf:
        points.append(person[RIGHT_EAR])

    # Fallback to shoulders (estimate head above them)
    if not points and conf[LEFT_SHOULDER] > min_conf and conf[RIGHT_SHOULDER] > min_conf:
        sx = (person[LEFT_SHOULDER][0] + person[RIGHT_SHOULDER][0]) / 2
        sy = (person[LEFT_SHOULDER][1] + person[RIGHT_SHOULDER][1]) / 2
        return sx, sy - 40  # vertical offset guess

    if not points:
        return None

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return sum(xs) / len(xs), sum(ys) / len(ys)



def draw_head(screen, img_x, img_y, person, conf, head_sprite):
    center = get_head_center(person, conf)
    if center is None:
        return

    cx, cy = center

    rect = head_sprite.get_rect()
    rect.center = (img_x + int(cx), img_y + int(cy))
    screen.blit(head_sprite, rect.topleft)
