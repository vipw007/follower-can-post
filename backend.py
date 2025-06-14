
import subprocess
import os
import zipfile
import requests
from flask_cors import CORS
from dotenv import load_dotenv  # Load environment variables

# Install required packages
subprocess.check_call(["pip", "install", "-q", "pyngrok", "flask", "pillow", "requests", "flask-cors", "python-dotenv"])

# Load environment variables
load_dotenv()

# Config from environment
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
PUBLIC_URL = os.getenv("PUBLIC_URL")
PORT = int(os.getenv("PORT", 10000))
CAPTION = "Code is 😊  #tech #codepoetry ##CodingMeme #FullStackDev #code #TechInstagram #js #ProgrammerLife #cybersecurity #hacking #bugbounty #linux #infosec"

# Download font
url = "https://drive.google.com/uc?export=download&id=1nTlvvCmfyxniWnQRpIg4EC6wbUk7_Fwb"
response = requests.get(url)
with open("JetBrains_Mono.zip", "wb") as f:
    f.write(response.content)

os.makedirs("fonts", exist_ok=True)
with zipfile.ZipFile("JetBrains_Mono.zip", "r") as zip_ref:
    zip_ref.extractall("fonts")

# Kill port 5050 processes and ngrok
try:
    subprocess.run(["fuser", "-k", "5050/tcp"], check=True)
except Exception:
    pass
try:
    subprocess.run(["pkill", "-f", "ngrok"], check=True)
except Exception:
    pass

# Flask app
from flask import Flask, request, send_file, jsonify
from pyngrok import ngrok
from PIL import Image, ImageDraw, ImageFont
import threading, time, re

FONT_PATH = "fonts/JetBrainsMono-Italic-VariableFont_wght.ttf"
IMG_PATH = "poetry.png"

ngrok.set_auth_token("2y7V0oDHegL0t8fmCr8efub9PFn_6ijcYdeaRQaQsy9A7CUh3")

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "https://vivekyadav2o.netlify.app"], methods=["GET", "POST", "OPTIONS"])


# Color styling
def style_code_line(code):
    token_pattern = r'"[^"]*"|'[^']*'|\w+|[^\w\s]'
    tokens = re.findall(token_pattern, code)
    parts = []
    keywords = {'if', 'else', 'return', 'function', 'for', 'while', 'const', 'let', 'var'}
    for i, token in enumerate(tokens):
        if token in keywords:
            parts.append((token, "#8be9fd"))
        elif token == '.':
            parts.append((token, "#ff79c6"))
        elif i > 0 and tokens[i-1] == '.':
            parts.append((token, "#f1fa8c"))
        elif token.startswith('"') or token.startswith("'"):
            parts.append((token, "#50fa7b"))
        elif re.match(r'^\d+$', token):
            parts.append((token, "#bd93f9"))
        elif token in {'(', ')', ';', '=', '=>', ','}:
            parts.append((token, "#ffffff"))
        else:
            parts.append((token, "#ff79c6"))
    return parts

def draw_code_line(draw, x, y, parts, font):
    for text, color in parts:
        draw.text((x, y), text, font=font, fill=color)
        x += draw.textlength(text, font=font)

def generate_poetry_image(line1, line2, line3, output_path=IMG_PATH):
    width, height = 1080, 1080
    img = Image.new('RGB', (width, height), color=(40, 42, 54))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 38)
    code_lines = [
        style_code_line(line1),
        style_code_line(line2) if line2 else [],
        style_code_line(line3) if line3 else []
    ]
    spacing, start_y, x_start = 70, 280, 60
    for i, parts in enumerate(code_lines):
        if not parts:
            continue
        y = start_y + i * spacing
        draw_code_line(draw, x_start, y, parts, font)
    wm = "#poetic_coder"
    wm_font = ImageFont.truetype(FONT_PATH, 30)
    draw.text((width - draw.textlength(wm, wm_font) - 30, height - 90), wm, font=wm_font, fill=(200, 200, 200))
    img.save(output_path)

def post_to_instagram(image_url):
    creation_resp = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",
        data={'image_url': image_url, 'caption': CAPTION, 'access_token': ACCESS_TOKEN}
    )
    if creation_resp.status_code != 200:
        return f"Media creation failed: {creation_resp.json()}"
    creation_id = creation_resp.json().get("id")
    publish_resp = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish",
        data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}
    )
    return "🎉 Posted!" if publish_resp.status_code == 200 else f"Publish failed: {publish_resp.json()}"

@app.route("/poetry", methods=["POST", "OPTIONS"])
def poetry_api():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json()
    text = data.get("text", "")

    # Split by comma and trim spaces
    lines = [line.strip() for line in text.split(",")]

    # Support up to 3 lines
    l1 = lines[0] if len(lines) > 0 else ""
    l2 = lines[1] if len(lines) > 1 else ""
    l3 = lines[2] if len(lines) > 2 else ""

    generate_poetry_image(l1, l2, l3)
    time.sleep(1)
    image_url = f"{PUBLIC_URL}/poetry.png"
    result = post_to_instagram(image_url)
    return jsonify({"image_url": image_url, "status": result})

@app.route("/poetry.png")
def serve_image():
    return send_file(IMG_PATH, mimetype='image/png')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
