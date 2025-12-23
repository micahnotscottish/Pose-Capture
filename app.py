import threading
from flask_app import app
from cloudflared import start_cloudflared
from config import FLASK_PORT
from game.main import myGame

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=FLASK_PORT, threaded=True ), daemon=True).start()

    cloudflared_proc, public_url = start_cloudflared()
    
    mygame = myGame()
    mygame.run_pygame_loop()
        
    cloudflared_proc.terminate()
