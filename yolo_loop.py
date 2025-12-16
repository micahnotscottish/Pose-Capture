import cv2
import sys
from ultralytics import YOLO
from config import YOLO_MODEL_PATH
import flask_app


def run_yolo_loop():
    model = YOLO(YOLO_MODEL_PATH)

    print("Starting YOLO loop. Press 'q' to exit.")

    while True:
        if flask_app.latest_frame is not None and not flask_app.processing:
            flask_app.processing = True

            frame = flask_app.latest_frame.copy()
            flask_app.latest_frame = None

            results = model(frame)
            annotated = results[0].plot()

            cv2.imshow("YOLO Pose Tracking (Phone Camera)", annotated)

            flask_app.processing = False

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()
    sys.exit(0)
