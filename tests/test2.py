from flask import Flask, render_template, request
import numpy as np
import cv2
from ultralytics import YOLO
import threading

app = Flask(__name__)

model = YOLO("yolov8n-pose.pt")

latest_frame = None

processing = False

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    global latest_frame, processing

    if processing:
        return "BUSY", 204

    np_arr = np.frombuffer(request.data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is not None:
        latest_frame = frame

    return "OK"


def yolo_loop():
    global latest_frame, processing

    while True:
        if latest_frame is not None and not processing:
            processing = True

            frame = latest_frame.copy()
            latest_frame = None

            results = model(frame)
            annotated = results[0].plot()

            cv2.imshow("YOLO Pose Tracking (Phone Camera)", annotated)

            processing = False

        # IMPORTANT: must run every loop on Windows
        cv2.waitKey(1)



if __name__ == "__main__":
    threading.Thread(target=yolo_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8080, threaded=True)

