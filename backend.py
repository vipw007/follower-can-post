import os
import re
import time
import requests
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

# Load environment variables
load_dotenv()

# Config from environment
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
PUBLIC_URL = os.getenv("PUBLIC_URL")
PORT = int(os.getenv("PORT", 10000))

# Constants
CAPTION = "Code is 😊 #cybersecurity #hacking #bugbounty #linux #infosec #tech #codepoetry #CodingMeme #FullStackDev #code #TechInstagram #js #ProgrammerLife"
FONT_PATH = "fonts/JetBrainsMono-Italic-VariableFont_wght.ttf"
STATIC_PATH = "static"
IMG_FILENAME = "poetry.png"
IMG_PATH = os.path.join(STATIC_PATH, IMG_FILENAME)

# Ensure static directory exists
os.makedirs(STATIC_PATH, exist_ok=True)

# Setup Flask app
app = Flask(__name__, static_url_path="/static")
CORS(app, origins=["http://localhost:5173", "https://vivekyadav2o.netlify.app"], methods=["GET", "POST", "OPTIONS"])


# Syntax color styling
def style_code_line(code):
    token_pattern = r'"[^"]*"|\'[^\']*\'|\w+|[^\w\s]'
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
    code_lines = [style_code_line(line) for line in [line1, line2, line3] if line]
    spacing, start_y, x_start = 70, 280, 60
    for i, parts in enumerate(code_lines):
        y = start_y + i * spacing
        draw_code_line(draw, x_start, y, parts, font)
    # Watermark
    wm = "#poetic_coder"
    wm_font = ImageFont.truetype(FONT_PATH, 30)
    draw.text((width - draw.textlength(wm, wm_font) - 30, height - 90), wm, font=wm_font, fill=(200, 200, 200))
    img.save(output_path)


def post_to_instagram(image_url):
    # Step 1: create media
    creation_resp = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",
        data={
            'image_url': image_url,
            'caption': CAPTION,
            'access_token': ACCESS_TOKEN
        }
    )
    if creation_resp.status_code != 200:
        return f"Media creation failed: {creation_resp.json()}"

    creation_id = creation_resp.json().get("id")

    # Step 2: publish media
    publish_resp = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish",
        data={
            'creation_id': creation_id,
            'access_token': ACCESS_TOKEN
        }
    )
    return "🎉 Posted!" if publish_resp.status_code == 200 else f"Publish failed: {publish_resp.json()}"


@app.route("/poetry", methods=["POST", "OPTIONS"])
def poetry_api():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json()

    # Accept both single text and 3-line input
    if "text" in data:
        lines = [line.strip() for line in re.split(r"[,\n]", data.get("text", "")) if line.strip()]
    else:
        lines = [data.get(f"line{i}", "").strip() for i in range(1, 4)]

    # Ensure max 3 lines
    lines = (lines + ["", "", ""])[:3]
    l1, l2, l3 = lines

    # Generate image
    generate_poetry_image(l1, l2, l3)
    time.sleep(1)

    image_url = f"{PUBLIC_URL}/static/{IMG_FILENAME}"
    result = post_to_instagram(image_url)
    return jsonify({"image_url": image_url, "status": result})


# Optional health check
@app.route("/")
def index():
    return "Server running."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
