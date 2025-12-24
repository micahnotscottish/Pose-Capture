import cv2
import pygame
import numpy as np
from ultralytics import YOLO

# pygame
pygame.init()
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("YOLOv8 Pose - All Keypoints")
clock = pygame.time.Clock()

# model
model = YOLO("yolo11n-pose.pt")

# camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

# main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    success, frame = cap.read()
    if not success:
        continue

    # run pose detection
    results = model(frame, verbose=False)

    # convert frame
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # convert to Pygame surface
    frame_surface = pygame.surfarray.make_surface(np.rot90(frame_rgb))

    # draw camera feed
    screen.blit(frame_surface, (0, 0))

    # draw keypoints
    if results and results[0].keypoints is not None:
        kpts = results[0].keypoints

        xy = kpts.xy.cpu().numpy()
        conf = kpts.conf.cpu().numpy()

        if xy.size > 0:
            person = xy[0]
            person_conf = conf[0]

            for i in range(17):
                x, y = person[i]
                c = person_conf[i]

                if c > 0.5:
                    pygame.draw.circle(screen, (255, 0, 0), (WIDTH - int(x), int(y)), 8)

    pygame.display.flip()
    clock.tick(30)
cap.release()
pygame.quit()
