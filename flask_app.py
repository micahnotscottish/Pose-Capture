from flask import Flask, render_template, request
import numpy as np
import cv2

app = Flask(__name__, template_folder="website", static_folder="website")

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
