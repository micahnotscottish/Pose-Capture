import pygame
import random
import sys




class MeteorGame:
    def __init__(self):
        
        # Global list to store meteors
        self.meteors = []

        # Global score
        self.score = 0
        


    def spawn_meteor(self, screen_width):
        """
        Spawn a meteor at a random horizontal position.
        Types: 'good' (green) or 'bad' (red)
        """
        x = random.randint(0, screen_width - 30)
        y = -30
        speed = random.randint(3, 7)
        size = random.randint(20, 50)
        meteor_type = random.choice(['good', 'bad'])
        color = (0, 200, 0) if meteor_type == 'good' else (200, 0, 0)
        self.meteors.append({
            "x": x,
            "y": y,
            "speed": speed,
            "size": size,
            "type": meteor_type,
            "color": color
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
            pygame.draw.circle(screen, meteor["color"], (meteor["x"], meteor["y"]), meteor["size"])

            if player_rect:
                if self.rect_circle_collision(player_rect, meteor["x"], meteor["y"], meteor["size"]):
                    if meteor["type"] == "good":
                        self.score += 1
                        self.meteors.remove(meteor)
                    else:
                        # Bad meteor hit → show points and quit
                        txt = score_font.render(f"Final Score: {self.score}", True, (255, 255, 255))
                        screen.blit(txt, (screen.get_width() // 2 - 80, screen.get_height() // 2 - 20))
                        pygame.display.flip()
                        pygame.time.delay(2000)
                        pygame.quit()
                        sys.exit()

        # Remove meteors off-screen
        self.meteors[:] = [m for m in self.meteors if m["y"] - m["size"] < screen.get_height()]

        # Draw current score
        score_txt = score_font.render(f"Score: {self.score}", True, (0, 0, 0), (255,0,0))
        screen.blit(score_txt, (10, 10))
