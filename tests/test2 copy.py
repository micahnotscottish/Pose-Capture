from flask import Flask, render_template, request
import numpy as np
import cv2
from ultralytics import YOLO
import threading
import subprocess
import sys
import re
import qrcode

# ---- Config ----
CLOUDFLARED_PATH = "C:\\Program Files (x86)\\cloudflared\\cloudflared.exe"
FLASK_PORT = 8080

# ---- Flask app ----
app = Flask(__name__)
model = YOLO("yolo11n-pose.pt")
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

# ---- YOLO loop (main thread) ----
def yolo_loop():
    global latest_frame, processing
    print("Starting YOLO loop. Press 'q' in the window to exit.")
    while True:
        if latest_frame is not None and not processing:
            processing = True
            frame = latest_frame.copy()
            latest_frame = None

            results = model(frame)
            annotated = results[0].plot()

            cv2.imshow("YOLO Pose Tracking (Phone Camera)", annotated)
            processing = False

        # Main thread waitKey
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("Exit requested. Closing...")
            break

    cv2.destroyAllWindows()
    sys.exit(0)

# ---- Start Cloudflare Tunnel ----
def start_cloudflared():
    print("Starting Cloudflare Tunnel...")
    proc = subprocess.Popen(
        [CLOUDFLARED_PATH, "tunnel", "--url", f"http://localhost:{FLASK_PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    public_url = None
    url_pattern = re.compile(r"https://[a-z0-9\-]+\.trycloudflare\.com")
    while True:
        line = proc.stdout.readline()
        if line:
            match = url_pattern.search(line)
            if match:
                public_url = match.group(0)
                break

    print(f"Public URL: {public_url}")

    # Generate QR code (ASCII + PNG)
    qr = qrcode.QRCode()
    qr.add_data(public_url)
    qr.make(fit=True)
    qr.print_ascii()
    img = qr.make_image(fill_color="black", back_color="white")
    img.save("qr.png")
    print("QR code saved as qr.png. Scan it to open the site.")

    return proc, public_url

# ---- Main ----
if __name__ == "__main__":
    # Start Flask in a daemon thread
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=FLASK_PORT, threaded=True), daemon=True).start()

    # Start Cloudflare Tunnel
    cloudflared_proc, public_url = start_cloudflared()

    # Run YOLO loop in main thread
    yolo_loop()

    # Cleanup on exit
    cloudflared_proc.terminate()
