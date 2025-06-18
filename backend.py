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
    font = ImageFont.truetype(FONT_PATH, 38)

    code_lines = [style_code_line(line) for line in [line1, line2, line3] if line]
    spacing, start_y, x_start = 80, 450, 60  # Adjust as desired
for i, parts in enumerate(code_lines):
    y = start_y + i * spacing
    line_text = ''.join([text for text, _ in parts])
    text_width = draw.textlength(line_text, font=font)
    text_height = font.getbbox(line_text)[3]

    # Padding and style
    padding_x = 40
    padding_y = 25
    border_radius = 20
    card_fill = (55, 58, 75)         # Dark card color
    card_outline = (100, 100, 120)   # Subtle border
    shadow_offset = 5
    shadow_color = (20, 20, 30)

    # Center horizontally
    x_center = (width - text_width) // 2
    box_x0 = x_center - padding_x
    box_y0 = y - padding_y
    box_x1 = x_center + text_width + padding_x
    box_y1 = y + text_height + padding_y // 2

    # Draw shadow
    draw.rounded_rectangle(
        [box_x0 + shadow_offset, box_y0 + shadow_offset,
         box_x1 + shadow_offset, box_y1 + shadow_offset],
        radius=border_radius,
        fill=shadow_color
    )

    # Draw card background
    draw.rounded_rectangle(
        [box_x0, box_y0, box_x1, box_y1],
        radius=border_radius,
        fill=card_fill,
        outline=card_outline,
        width=2
    )

    # Draw text centered
    draw_code_line(draw, x_center, y, parts, font)
    # Watermark - use custom or default
    watermark = f"#{author}" if author else "#poetic_coder"
    wm_font = ImageFont.truetype(FONT_PATH, 30)
    draw.text((width - draw.textlength(watermark, wm_font) - 30, height - 90), watermark, font=wm_font, fill=(200, 200, 200))

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
