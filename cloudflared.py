import subprocess
import re
import qrcode
from config import CLOUDFLARED_PATH, FLASK_PORT


def start_cloudflared():
    print("Starting Cloudflare Tunnel...")

    proc = subprocess.Popen(
        [CLOUDFLARED_PATH, "tunnel", "run", "nobread"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    """"
    url_pattern = re.compile(r"https://[a-z0-9\-]+\.trycloudflare\.com")

    public_url = None
    while True:
        line = proc.stdout.readline()
        if line:
            match = url_pattern.search(line)
            if match:
                public_url = match.group(0)
                break

    print(f"Public URL: {public_url}")

    qr = qrcode.QRCode()
    qr.add_data(public_url)
    qr.make(fit=True)
    qr.print_ascii()

    img = qr.make_image(fill_color="black", back_color="white")
    img.save("qrcode/qr.png")

    print("QR code saved as qr.png")
    """
    public_url = None
    return proc, public_url
