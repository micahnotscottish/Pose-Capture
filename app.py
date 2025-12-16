import threading
from flask_app import app
from cloudflared import start_cloudflared
from yolo_loop import run_yolo_loop
from config import FLASK_PORT


if __name__ == "__main__":
    threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0",
            port=FLASK_PORT,
            threaded=True
        ),
        daemon=True
    ).start()

    cloudflared_proc, public_url = start_cloudflared()

    try:
        run_yolo_loop()
    finally:
        cloudflared_proc.terminate()
