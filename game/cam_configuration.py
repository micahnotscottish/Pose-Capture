import pygame
import flask_app
import cv2

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