import cv2
import pygame
import numpy as np
from ultralytics import YOLO

# -------------------- Pygame Setup --------------------
pygame.init()
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("YOLOv8 Pose - All Keypoints")
clock = pygame.time.Clock()

# -------------------- YOLO Model --------------------
model = YOLO("yolo11n-pose.pt")

# -------------------- Camera --------------------
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

# -------------------- Main Loop --------------------
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    success, frame = cap.read()
    if not success:
        continue

    # Run pose detection
    results = model(frame, verbose=False)

    # Convert OpenCV frame (BGR) -> RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert to Pygame surface
    frame_surface = pygame.surfarray.make_surface(
        np.rot90(frame_rgb)
    )

    # Draw camera feed
    screen.blit(frame_surface, (0, 0))

    # -------------------- Draw Keypoints --------------------
    if results and results[0].keypoints is not None:
        kpts = results[0].keypoints

        xy = kpts.xy.cpu().numpy()      # (people, 17, 2)
        conf = kpts.conf.cpu().numpy()  # (people, 17)

        if xy.size > 0:
            person = xy[0]
            person_conf = conf[0]

            for i in range(17):
                x, y = person[i]        # keypoints
                c = person_conf[i]      # confidence

                if c > 0.5:
                    pygame.draw.circle(
                        screen,
                        (255, 0, 0),
                        (WIDTH - int(x), int(y)),  # invert x-axis only
                        8
                        )


    pygame.display.flip()
    clock.tick(30)

# -------------------- Cleanup --------------------
cap.release()
pygame.quit()
