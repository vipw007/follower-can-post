import os
import re
import time
import requests
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
PORT = int(os.getenv("PORT", 10000))
IMG_FILENAME = "poetry.png"
FONT_PATH = os.path.join("fonts", "JetBrainsMono-Italic-VariableFont_wght.ttf")
CAPTION = "Code is poetry.\n\n#cybersecurity #hacking #bugbounty #linux #infosec #tech #codepoetry #CodingMeme #FullStackDev #code #TechInstagram #js #ProgrammerLife"

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "https://vivekyadav2o.netlify.app", "https://poet-code.vercel.app"], methods=["GET", "POST", "OPTIONS"])

# --- Helper Functions ---

def style_code_line(code):
    token_pattern = r'"[^"]*"|\'[^\']*\'|\w+|[^\w\s]'
    tokens = re.findall(token_pattern, code)
    parts = []
    keywords = {'if', 'else', 'return', 'function', 'for', 'while', 'const', 'let', 'var', 'raiseException', 'throw'}
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
        elif token in {'(', ')', ';', '=', '=>', ',', ':'}:
            parts.append((token, "#ffffff"))
        else:
            parts.append((token, "#ff79c6"))
    return parts

    # Initial font size
    base_font_size = 42
    font = ImageFont.truetype(FONT_PATH, base_font_size)
    
    # Determine the width of the longest line
    longest_line_width = max(
        [draw.textlength("".join([text for text, _ in line]), font=font) for line in code_lines],
        default=0
    )
    max_card_width = width - 100  # screen edge padding
    
    # Scale down font size if needed
    if longest_line_width + 160 > max_card_width:  # 160 is padding buffer
        shrink_ratio = (max_card_width - 160) / longest_line_width
        font_size = max(int(base_font_size * shrink_ratio), 26)  # don't go below 26
        font = ImageFont.truetype(FONT_PATH, font_size)
    else:
        font_size = base_font_size


def fit_font_size(draw, text, max_width, font_path, base_size=40, min_size=28):
    for size in range(base_size, min_size - 1, -1):
        font = ImageFont.truetype(font_path, size)
        if draw.textlength(text, font=font) <= max_width:
            return font
    return ImageFont.truetype(font_path, min_size)

def draw_code_line(draw, x, y, parts, font):
    for text, color in parts:
        draw.text((x, y), text, font=font, fill=color)
        x += draw.textlength(text, font=font)

def generate_poetry_image(*lines, author=None, output_path=IMG_FILENAME):
    width, height = 1080, 1080
    strip_height = 40
    padding_x, padding_y = 30, 30
    spacing = 80

    img = Image.new('RGB', (width, height), color=(40, 42, 54))
    draw = ImageDraw.Draw(img)

    # Prepare lines
    raw_lines = [line for line in lines if line]
    code_lines = []
    fonts_per_line = []
    for line in raw_lines:
        text = ''.join(re.findall(r'"[^"]*"|\'[^\']*\'|\w+|[^\w\s]', line))
        font = fit_font_size(draw, text, width - 120, FONT_PATH)
        fonts_per_line.append(font)
        code_lines.append(style_code_line(line))

    line_heights = len(code_lines) * spacing
    longest_line = max(
        [draw.textlength("".join([text for text, _ in line]), font=fonts_per_line[i]) for i, line in enumerate(code_lines)],
        default=0
    )
    max_card_width = width - 100  # e.g. 980px if width is 1080
    card_width = min(int(longest_line + padding_x * 2), max_card_width)

    card_height = int(line_heights + padding_y * 2 + strip_height)

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

    # Draw top strip like Mac editor
    draw.rectangle([card_x, card_y, card_x + card_width, card_y + strip_height], fill=(65, 67, 84))
    r = 8
    for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = card_x + 20 + i * 24
        cy = card_y + strip_height // 2
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    # Draw code lines
    for i, parts in enumerate(code_lines):
        font = fonts_per_line[i]
        x = card_x + padding_x
        y = card_y + padding_y + strip_height + i * spacing
        draw_code_line(draw, x, y, parts, font)

    # Watermark
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

    lines = []
    if "text" in data:
        lines = [line.strip() for line in re.split(r"[\n,]", data["text"]) if line.strip()]
    else:
        for i in range(1, 6):
            line = data.get(f"line{i}", "").strip()
            if line:
                lines.append(line)

    lines = (lines + ["", "", "", "", ""])[:5]
    author = data.get("author", "").strip()

    generate_poetry_image(*lines, author=author)
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
