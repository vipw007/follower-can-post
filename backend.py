import os
import re
import time
import requests
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# /Load .env environment variables
load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
PORT = int(os.getenv("PORT", 10000))
IMG_FILENAME = "poetry.png"
FONT_PATH = os.path.join("fonts", "JetBrainsMono-Italic-VariableFont_wght.ttf")

CAPTION = "Code is 😊 \n\n\n  \n \n \n \n \n \n \n \n \n \n \n \n #cybersecurity #hacking #bugbounty #linux #infosec #tech #codepoetry #CodingMeme #FullStackDev #code #TechInstagram #js #ProgrammerLife"

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "https://vivekyadav2o.netlify.app", "https://poet-code.vercel.app"], methods=["GET", "POST", "OPTIONS"])

# --- Helper Functions ---

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

def generate_poetry_image(line1, line2, line3, author=None, output_path=IMG_FILENAME):
    width, height = 1080, 1350
    img = Image.new('RGB', (width, height), color=(40, 42, 54))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 42)

    # Prepare lines
    code_lines = [style_code_line(line) for line in [line1, line2, line3] if line]
    spacing = 75
    padding_x, padding_y = 60, 60
    line_heights = len(code_lines) * spacing

    # Measure card size
    longest_line = max(
        [draw.textlength("".join([text for text, _ in line]), font=font) for line in code_lines],
        default=0
    )
    card_width = int(longest_line + padding_x * 2)
    card_height = int(line_heights + padding_y * 2)

    # Center card position
    card_x = (width - card_width) // 2
    card_y = (height - card_height) // 2

    # Draw shadow
    shadow_offset = 10
    shadow_color = (30, 30, 30)
    draw.rounded_rectangle(
        [card_x + shadow_offset, card_y + shadow_offset, card_x + card_width + shadow_offset, card_y + card_height + shadow_offset],
        radius=30,
        fill=shadow_color
    )

    # Draw card
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_width, card_y + card_height],
        radius=30,
        fill=(50, 52, 70)
    )

    # Draw code lines centered in the card
    for i, parts in enumerate(code_lines):
        total_line_width = sum(draw.textlength(text, font=font) for text, _ in parts)
        x_start = card_x + (card_width - total_line_width) // 2
        y = card_y + padding_y + i * spacing
        draw_code_line(draw, x_start, y, parts, font)

    # Draw watermark
    watermark = f"#{author}" if author else "#poetic_coder"
    wm_font = ImageFont.truetype(FONT_PATH, 30)
    wm_x = width - draw.textlength(watermark, font=wm_font) - 30
    wm_y = height - 90
    draw.text((wm_x, wm_y), watermark, font=wm_font, fill=(200, 200, 200))

    img.save(output_path)



def post_to_instagram(image_url):
    create_resp = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",
        data={
            'image_url': image_url,
            'caption': CAPTION,
            'access_token': ACCESS_TOKEN
        }
    )
    if create_resp.status_code != 200:
        return f"Media creation failed: {create_resp.json()}"

    creation_id = create_resp.json().get("id")
    publish_resp = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish",
        data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}
    )
    return "🎉 Posted!" if publish_resp.status_code == 200 else f"Publish failed: {publish_resp.json()}"

# --- Routes ---

@app.route("/poetry", methods=["POST", "OPTIONS"])
def poetry_api():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    # Support both 'text' and line1/line2/line3
    if "text" in data:
        lines = [line.strip() for line in re.split(r"[,\n]", data["text"]) if line.strip()]
    else:
        lines = [data.get(f"line{i}", "").strip() for i in range(1, 4)]

    lines = (lines + ["", "", ""])[:3]
    l1, l2, l3 = lines

    author = data.get("author", "").strip()

    generate_poetry_image(l1, l2, l3, author=author)
    time.sleep(1)

    base_url = request.host_url.rstrip('/')
    image_url = f"{base_url}/{IMG_FILENAME}"

    result = post_to_instagram(image_url)
    return jsonify({"image_url": image_url, "status": result})


@app.route(f"/{IMG_FILENAME}")
def serve_image():
    return send_file(IMG_FILENAME, mimetype='image/png')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
