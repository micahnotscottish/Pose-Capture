import pygame
import random
import sys




class MeteorGame:
    def __init__(self):
        
        # Global list to store meteors
        self.meteors = []

        # Global score
        self.score = 0
        
        self.m1sprite = pygame.image.load("sprites/meteor1.png").convert_alpha()
        self.m2sprite = pygame.image.load("sprites/meteor2.png").convert_alpha()
        self.egg = pygame.image.load("sprites/egg.png").convert_alpha()
        
        self.meteor_scale_range = (0.2, .5)   # 👈 adjust size range here
        self.flicker_interval = 120            # ms between sprite swaps


    def spawn_meteor(self, screen_width):
        x = random.randint(0, screen_width - 60)
        y = -150
        speed = random.randint(3, 7)

        scale = random.uniform(*self.meteor_scale_range)
        meteor_type = random.choice(["good", "bad"])

        if meteor_type == "good":
            base_sprite = self.egg
            alt_sprite = None
        else:
            base_sprite = self.m1sprite
            alt_sprite = self.m2sprite

        sprite = pygame.transform.scale_by(base_sprite, scale)

        self.meteors.append({
            "x": x,
            "y": y,
            "speed": speed,
            "type": meteor_type,

            # sprite handling
            "sprite": sprite,
            "base_sprite": base_sprite,
            "alt_sprite": alt_sprite,
            "scale": scale,
            "use_alt": False,
            "last_flicker": pygame.time.get_ticks(),

            # collision size
            "radius": sprite.get_width() // 2
        })


    def rect_circle_collision(self, rect, cx, cy, radius):
        """
        Check collision between a rectangle and a circle.
        """
        closest_x = max(rect.left, min(cx, rect.right))
        closest_y = max(rect.top, min(cy, rect.bottom))
        dx = cx - closest_x
        dy = cy - closest_y
        return (dx*dx + dy*dy) < (radius*radius)

    def update_and_draw_meteors(self, screen, player_rect):
        """
        Update meteor positions, draw them on the screen,
        handle collisions with player, update score, and quit if bad meteor.
        """
        global score
        font = pygame.font.SysFont(None, 36)
        score_font = pygame.font.SysFont(None, 72)

        for meteor in self.meteors[:]:
            meteor["y"] += meteor["speed"]

            # --- Flicker between meteor1 & meteor2 ---
            if meteor["alt_sprite"]:
                now = pygame.time.get_ticks()
                if now - meteor["last_flicker"] > self.flicker_interval:
                    meteor["use_alt"] = not meteor["use_alt"]
                    sprite_source = meteor["alt_sprite"] if meteor["use_alt"] else meteor["base_sprite"]
                    meteor["sprite"] = pygame.transform.scale_by(sprite_source, meteor["scale"])
                    meteor["last_flicker"] = now

            screen.blit(meteor["sprite"], (meteor["x"], meteor["y"]))

            if player_rect:
                cx = meteor["x"] + meteor["radius"]
                cy = meteor["y"] + meteor["radius"]

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


        # Remove meteors off-screen
        self.meteors[:] = [
        m for m in self.meteors
        if m["y"] - m["radius"] < screen.get_height()
]



        # Draw current score
        score_txt = score_font.render(f"Score: {self.score}", True, (0, 0, 0), (255,0,0))
        screen.blit(score_txt, (10, 10))
