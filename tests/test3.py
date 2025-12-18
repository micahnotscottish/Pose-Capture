import cv2
import pygame
from ultralytics import YOLO
import numpy as np

# Initialize Pygame
pygame.init()
screen_width, screen_height = 640, 480
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("YOLO Pose Tracking in Pygame")
clock = pygame.time.Clock()

# Load the YOLOv8 pose model
# You can use 'yolov8n-pose.pt' for a lightweight model
model = YOLO('yolov8n-pose.pt')

# Initialize webcam capture
cap = cv2.VideoCapture(0) # 0 for default webcam
if not cap.isOpened():
    print("Cannot open camera")
    exit()

# Main application loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Capture frame-by-frame from webcam
    success, frame = cap.read()
    if success:
        # Run YOLO pose inference on the frame
        results = model(frame, verbose=False)

        # Get keypoints from the first detected person (if any)
        if results and results[0].keypoints.xy.cpu().numpy().size > 0:
            keypoints = results[0].keypoints.xy.cpu().numpy()[0]
            # Keypoints are an array where each row is [x, y, confidence]

            # Choose a specific keypoint to attach the object to (e.g., the nose, which is index 0)
            nose_x, nose_y = int(keypoints[0][0]), int(keypoints[0][1])

            # Clear the Pygame screen
            screen.fill((0, 0, 0)) # Fill with black

            # Draw the Pygame object at the nose keypoint's coordinates
            # Pygame uses (x, y) where (0, 0) is the top-left corner
            pygame.draw.circle(screen, (255, 0, 0), (nose_x, nose_y), 15) # Red circle with radius 15

            # You can also use Pygame's blit function to display an image at the coordinates
            # e.g., screen.blit(my_image, (nose_x, nose_y))

            # Update the Pygame display
            pygame.display.flip()

    # Cap the frame rate
    clock.tick(30)

# After the loop release the camera and close pygame
cap.release()
pygame.quit()
