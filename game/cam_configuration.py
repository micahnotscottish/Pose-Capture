import pygame
import flask_app
import cv2

# This class displays and allows for the adjustment and configuration of the input camera capture.
# Adjustments are returned so they can be carried over into the game capture.
# Adjustments include:
# - cropping left and right sides
# - moving image left, right, up, and down
# - scaling the overall image
# call "configuration()" to run

class Configuration:
    def __init__(self, screen, initial_scale=1.0, initial_offx=0, initial_offy=0):
        self.screen = screen
        self.initial_scale = initial_scale
        self.initial_offx = initial_offx
        self.initial_offy = initial_offy
        self.clock = pygame.time.Clock()
        self.win_w, self.win_h = self.screen.get_size()

        # Preview image will be updated each loop from a live frame if available
        self.preview_surf = None
        self.ph = self.pw = 0

        # Variables for slider mappings, as well as min and max values available
        self.SCALE_MIN = 0.2
        self.SCALE_MAX = 3.0
        self.t_scale = max(0.0, min(1.0, (self.initial_scale - self.SCALE_MIN) / (self.SCALE_MAX - self.SCALE_MIN)))
        self.max_offx = self.win_w // 2
        self.max_offy = self.win_h // 2
        self.t_offx = (self.initial_offx + self.max_offx) / (2 * self.max_offx) if self.max_offx else 0.5
        self.t_offy = (self.initial_offy + self.max_offy) / (2 * self.max_offy) if self.max_offy else 0.5
        self.t_crop_left = 0.0
        self.t_crop_right = 1.0

        self.dragging = None
        self.running = True
        self.font = pygame.font.SysFont(None, 28)
        
    # This is a helper function to blit the rectangles and text of a slider to the screen
    def _draw_slider(self, surface, rect, t, label):
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

    # This is a helper function to quickly retrieve all sliders
    def _get_slider_rects(self):
        s1 = (50, self.win_h - 260, self.win_w - 100, 24)  # Scale
        s2 = (50, self.win_h - 220, self.win_w - 100, 24)  # Offset X
        s3 = (50, self.win_h - 180, self.win_w - 100, 24)  # Offset Y
        s4 = (50, self.win_h - 140, self.win_w - 100, 24)  # Crop Left
        s5 = (50, self.win_h - 100, self.win_w - 100, 24)  # Crop Right
        return s1, s2, s3, s4, s5

    # This function maps the slider values to the correlated value in the range available
    def _map_t_values(self):
        scale = self.SCALE_MIN + self.t_scale * (self.SCALE_MAX - self.SCALE_MIN)
        offx = int(round(self.t_offx * 2 * self.max_offx - self.max_offx))
        offy = int(round(self.t_offy * 2 * self.max_offy - self.max_offy))
        return scale, offx, offy, self.t_crop_left, self.t_crop_right

    # This function grabs a preview image of the raw camera input
    def _update_preview(self):
        live = None
        try:
            if flask_app.latest_frame is not None:
                live = flask_app.latest_frame.copy()
        except Exception:
            live = None

        if live is not None:
            try:
                h, w = live.shape[:2]
                
                # compute crop pixels
                left_px = int(self.t_crop_left * w)
                right_px = int(self.t_crop_right * w)
                
                # safety clamp
                if right_px - left_px > 10:
                    live = live[:, left_px:right_px]
                preview = cv2.cvtColor(live, cv2.COLOR_BGR2RGB)
                self.ph, self.pw = preview.shape[:2]
                self.preview_surf = pygame.image.frombuffer(preview.tobytes(), (self.pw, self.ph), 'RGB')
            except Exception:
                self.preview_surf = None

    # Draw ui and image preview adjusted as done by the sliders
    def _draw_preview_and_ui(self):
        self.screen.fill((30, 30, 30))
        # preview centered (if available)
        if self.preview_surf is not None and self.pw > 0 and self.ph > 0:
            # map t_scale to real scale
            scale_val = self.SCALE_MIN + self.t_scale * (self.SCALE_MAX - self.SCALE_MIN)

            # compute a base fit scale so the preview fits comfortably in the UI
            max_preview_w = int(self.win_w * 0.8)
            max_preview_h = int(self.win_h * 0.6)
            base_fit = min(max_preview_w / float(self.pw), max_preview_h / float(self.ph))

            final_w = max(1, int(round(self.pw * base_fit * scale_val)))
            final_h = max(1, int(round(self.ph * base_fit * scale_val)))

            scaled = pygame.transform.smoothscale(self.preview_surf, (final_w, final_h))

            # compute offsets in pixels from t_offx/t_offy
            max_offx_preview = self.win_w // 2
            max_offy_preview = self.win_h // 2
            offx_px = int(round(self.t_offx * 2 * max_offx_preview - max_offx_preview))
            offy_px = int(round(self.t_offy * 2 * max_offy_preview - max_offy_preview))

            pv_x = (self.win_w // 2 - final_w // 2) + offx_px
            pv_y = (self.win_h // 2 - final_h // 2 - 60) + offy_px
            self.screen.blit(scaled, (pv_x, pv_y))
        
        else:
            # placeholder box
            placeholder = pygame.Rect(self.win_w // 2 - 320, self.win_h // 2 - 240 - 60, 640, 480)
            pygame.draw.rect(self.screen, (50, 50, 50), placeholder)
            no_txt = pygame.font.SysFont(None, 24).render('Waiting for camera...', True, (200, 200, 200))
            self.screen.blit(no_txt, (placeholder.x + 12, placeholder.y + 12))

        # get all slider rectangles available and draw them
        s1, s2, s3, s4, s5 = self._get_slider_rects()
        self._draw_slider(self.screen, s1, self.t_scale, 'Scale')
        self._draw_slider(self.screen, s2, self.t_offx, 'Offset X')
        self._draw_slider(self.screen, s3, self.t_offy, 'Offset Y')
        self._draw_slider(self.screen, s4, self.t_crop_left, 'Crop Left')
        self._draw_slider(self.screen, s5, self.t_crop_right, 'Crop Right')


        # draw calibration guide
        rect_w, rect_h = 100, 175
        rect_x = (self.screen.get_width() - rect_w) // 2
        rect_y = (self.screen.get_height() - rect_h) // 2 + 150
        pygame.draw.rect(self.screen, (255, 0, 0), (rect_x, rect_y, rect_w, rect_h), 4)
        font = pygame.font.SysFont(None, 32)
        text = "Adjust settings until body fits within this region"
        txt_surf = font.render(text, True, (255, 255, 255))
        txt_rect = txt_surf.get_rect(
        center=(self.screen.get_width() // 2, rect_y + rect_h + 20))
        self.screen.blit(txt_surf, txt_rect)

        # draw configure button
        self.cfg_rect = pygame.Rect(self.win_w // 2 - 80, self.win_h - 70, 160, 40)
        pygame.draw.rect(self.screen, (70, 140, 70), self.cfg_rect)
        txt = self.font.render('Configure', True, (255, 255, 255))
        txt_rect = txt.get_rect(center=self.cfg_rect.center)
        self.screen.blit(txt, txt_rect)


    # handle dragging of sliders
    def _handle_event(self, ev):
        if ev.type == pygame.QUIT:
            return 'quit'
        elif ev.type == pygame.MOUSEBUTTONDOWN:
            mx, my = ev.pos
            s1, s2, s3, s4, s5= self._get_slider_rects()
            if pygame.Rect(*s1).collidepoint(mx, my):
                self.dragging = ('scale', s1)
            elif pygame.Rect(*s2).collidepoint(mx, my):
                self.dragging = ('offx', s2)
            elif pygame.Rect(*s3).collidepoint(mx, my):
                self.dragging = ('offy', s3)
            elif pygame.Rect(*s4).collidepoint(mx, my):
                self.dragging = ('crop_left', s4)
            elif pygame.Rect(*s5).collidepoint(mx, my):
                self.dragging = ('crop_right', s5)
            else:
                if self.cfg_rect.collidepoint(mx, my):
                    return 'configure'
        elif ev.type == pygame.MOUSEBUTTONUP:
            self.dragging = None
        elif ev.type == pygame.MOUSEMOTION and self.dragging is not None:
            _, rect = self.dragging
            rx, ry, rw, rh = rect
            mx = ev.pos[0]
            t = (mx - rx) / float(max(1, rw))
            t = max(0.0, min(1.0, t))
            if self.dragging[0] == 'scale':
                self.t_scale = t
            elif self.dragging[0] == 'offx':
                self.t_offx = t
            elif self.dragging[0] == 'offy':
                self.t_offy = t
            elif self.dragging[0] == 'crop_left':
                self.t_crop_left = min(t, self.t_crop_right - 0.05)
            elif self.dragging[0] == 'crop_right':
                self.t_crop_right = max(t, self.t_crop_left + 0.05)

        return None


    # main function - calls event handling, updating, and drawing
    def configuration(self):
        while True:
            for ev in pygame.event.get():
                res = self._handle_event(ev)
                if res == 'quit':
                    return self.initial_scale, self.initial_offx, self.initial_offy, self.t_crop_left, self.t_crop_right
                if res == 'configure':
                    return self._map_t_values()

            self._update_preview()
            
            self._draw_preview_and_ui()

            pygame.display.flip()
            self.clock.tick(60)