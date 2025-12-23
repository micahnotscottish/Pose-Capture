import pygame
import random
import sys


# This is a quick and simple meteor avoiding game that I made to show off the motion capture capabilities
# You are a dinosaur that collects eggs to get points, but must avoid meteors in the process

class MeteorGame:
    def __init__(self):
        
        self.meteors = []
        self.score = 0
        
        # preload sprites
        self.m1sprite = pygame.image.load("sprites/meteor1.png").convert_alpha()
        self.m2sprite = pygame.image.load("sprites/meteor2.png").convert_alpha()
        self.egg = pygame.image.load("sprites/egg.png").convert_alpha()
    
        self.meteor_scale_range = (0.2, .5)
        self.flicker_interval = 120


    # spawn a meteor with slight randomization based on parameters
    def spawn_meteor(self, screen_width):
        x = random.randint(0, screen_width - 60)
        y = -150
        speed = random.randint(3, 7)
        scale = random.uniform(*self.meteor_scale_range)
        
        # "good" meteors are eggs and "bad" meteors are the meteors to avoid
        meteor_type = random.choice(["good", "bad"])

        if meteor_type == "good":
            base_sprite = self.egg
            alt_sprite = None
        else:
            # alt_sprite is used for animation of meteors
            base_sprite = self.m1sprite
            alt_sprite = self.m2sprite

        sprite = pygame.transform.scale_by(base_sprite, scale)

        # save meteor and its attributes
        self.meteors.append({
            "x": x,
            "y": y,
            "speed": speed,
            "type": meteor_type,
            "sprite": sprite,
            "base_sprite": base_sprite,
            "alt_sprite": alt_sprite,
            "scale": scale,
            "use_alt": False,
            "last_flicker": pygame.time.get_ticks(),
            "radius": sprite.get_width() // 2
        })


    def rect_circle_collision(self, rect, cx, cy, radius):
  
        closest_x = max(rect.left, min(cx, rect.right))
        closest_y = max(rect.top, min(cy, rect.bottom))
        dx = cx - closest_x
        dy = cy - closest_y
        return (dx*dx + dy*dy) < (radius*radius)


    # update positions and check and handle collisions with player
    def update_and_draw_meteors(self, screen, player_rect):

        global score
        score_font = pygame.font.SysFont(None, 72)

        for meteor in self.meteors[:]:
            meteor["y"] += meteor["speed"]

            # flicker between meteor sprites to create animation
            if meteor["alt_sprite"]:
                now = pygame.time.get_ticks()
                if now - meteor["last_flicker"] > self.flicker_interval:
                    meteor["use_alt"] = not meteor["use_alt"]
                    sprite_source = meteor["alt_sprite"] if meteor["use_alt"] else meteor["base_sprite"]
                    meteor["sprite"] = pygame.transform.scale_by(sprite_source, meteor["scale"])
                    meteor["last_flicker"] = now

            screen.blit(meteor["sprite"], (meteor["x"], meteor["y"]))

            # detect collisions with the player
            if player_rect:
                cx = meteor["x"] + meteor["radius"]
                cy = meteor["y"] + meteor["radius"]

                # if there is a collision, good collisions add a point and bad collisions end the game
                if self.rect_circle_collision(player_rect, cx, cy, meteor["radius"]):
                    if meteor["type"] == "good":
                        self.score += 1
                        self.meteors.remove(meteor)
                    else:
                        txt = score_font.render(f"Final Score: {self.score}", True, (255, 255, 255))
                        screen.blit(txt, (screen.get_width() // 2 - 100, screen.get_height() // 2))
                        pygame.display.flip()
                        pygame.time.delay(2000)
                        pygame.quit()
                        sys.exit()


        # remove meteors if they're no longer on screen
        new_meteors = []
        for meteor in self.meteors:
            if meteor["y"] - meteor["radius"] < screen.get_height():
                new_meteors.append(meteor)

        self.meteors = new_meteors

        # Draw current score
        score_txt = score_font.render(f"Score: {self.score}", True, (0, 0, 0), (255,0,0))
        screen.blit(score_txt, (10, 10))
