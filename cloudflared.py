import subprocess
import re
import qrcode
from config import CLOUDFLARED_PATH, FLASK_PORT


# this function starts the cloudflare tunnel using the domain name that I purchased
# originally I would open a temporary tunnel, which would give a randomly generated url,
# which I would generate a qr code from that the user would scan to join the game.
# It was pretty awesome.
# But unless you pay big moneys cloud flare limits the amount of tunnels you can open
# in quick succession under the same ip address, and with the amount of testing I was doing
# I would continually hit this limit.
# So alas, while the generated url and qrcode scanning was very epic, at least for this test version
# it uses a static cloudflare tunnel to my domain

def start_cloudflared():
    print("Starting Cloudflare Tunnel...")

    proc = subprocess.Popen(
        [CLOUDFLARED_PATH, "tunnel", "run", "nobread"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )


    # cool url regex getting and qr coode generation that i can't use :(
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
