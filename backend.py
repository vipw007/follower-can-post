import os
import re
import time
import requests
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# Load .env environment variables
load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
PORT = int(os.getenv("PORT", 10000))
IMG_FILENAME = "poetry.png"
FONT_PATH = os.path.join("fonts", "JetBrainsMono-Italic-VariableFont_wght.ttf")

CAPTION = "Code is 😊 \n\n\n  \n \n \n \n \n \n \n \n \n \n \n \n #cybersecurity #hacking #bugbounty #linux #infosec #tech #codepoetry #CodingMeme #FullStackDev #code #TechInstagram #js #ProgrammerLife"

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "https://vivekyadav2o.netlify.app", "https://poet-code.vercel.app"], methods=["GET", "POST", "OPTIONS"])

# --- Code Styling ---

def style_code_line(code):
    token_pattern = r'".*?"|\'.*?\'|\b\w+\b|[^\w\s]|\s+'
    tokens = re.findall(token_pattern, code)
    parts = []

    keywords = {'if', 'else', 'return', 'function', 'for', 'while', 'const', 'let', 'var', 'throw', 'new'}
    for i, token in enumerate(tokens):
        if token.isspace():
            parts.append((token, "#ffffff"))
        elif token in keywords:
            parts.append((token, "#8be9fd"))
        elif token == '.':
            parts.append((token, "#ff79c6"))
        elif i > 0 and tokens[i - 1] == '.':
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

def draw_code_line(draw, x, y, parts, font, max_width):
    line_x = x
    line_y = y
    for text, color in parts:
        word_width = draw.textlength(text, font=font)
        if line_x + word_width > x + max_width:
            line_x = x  # wrap to next line
            line_y += 60
        draw.text((line_x, line_y), text, font=font, fill=color)
        line_x += word_width
    return line_y + 60  # return new y after wrapping


# --- Image Generator ---

def generate_poetry_image(line1, line2, line3, line4=None, line5=None, author=None, output_path=IMG_FILENAME):
    width, height = 1080, 1350
    img = Image.new('RGB', (width, height), color=(40, 42, 54))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 42)

    # Prepare lines
    code_lines = [style_code_line(line) for line in [line1, line2, line3, line4, line5] if line]
    spacing = 75
    padding_x, padding_y = 80, 60  # Slightly increased padding_x
    line_heights = len(code_lines) * spacing

    # Measure card size
    longest_line = max(
        [draw.textlength("".join([text for text, _ in line]), font=font) for line in code_lines],
        default=0
    )
    max_card_width = width - 200  # Prevents card touching screen edges
    card_width = min(int(longest_line + padding_x * 2), max_card_width)
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
        # Draw macOS-style top strip
    strip_height = 40
    draw.rectangle(
        [card_x, card_y, card_x + card_width, card_y + strip_height],
        fill=(30, 32, 40)
    )
    
    # Draw red, yellow, green circles
    circle_radius = 10
    circle_spacing = 10
    circle_y = card_y + strip_height // 2
    circle_x = card_x + 20
    colors = [(255, 95, 86), (255, 189, 46), (39, 201, 63)]
    for color in colors:
        draw.ellipse(
            [circle_x - circle_radius, circle_y - circle_radius,
             circle_x + circle_radius, circle_y + circle_radius],
            fill=color
        )
        circle_x += circle_radius * 2 + circle_spacing


    current_y = card_y + padding_y + 60  # leave space for title strip
    for parts in code_lines:
        x_start = card_x + padding_x
        max_line_width = card_width - padding_x * 2
        current_y = draw_code_line(draw, x_start, current_y, parts, font, max_line_width)


    # Watermark
    watermark = f"#{author}" if author else "#poetic_coder"
    wm_font = ImageFont.truetype(FONT_PATH, 30)
    wm_x = width - draw.textlength(watermark, font=wm_font) - 30
    wm_y = height - 90
    draw.text((wm_x, wm_y), watermark, font=wm_font, fill=(200, 200, 200))

    img.save(output_path)

# --- Instagram API ---

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
    try:
        if request.method == "OPTIONS":
            return "", 200

        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid or missing JSON body"}), 400

        if "text" in data:
            lines = [line.strip() for line in re.split(r"[,\n]", data["text"]) if line.strip()]
        else:
            lines = [data.get(f"line{i}", "").strip() for i in range(1, 6)]  # Up to 5

        lines = (lines + [""] * 5)[:5]
        l1, l2, l3, l4, l5 = lines
        author = data.get("author", "").strip()

        generate_poetry_image(l1, l2, l3, l4, l5, author=author)

        time.sleep(1)
        base_url = request.host_url.rstrip('/')
        image_url = f"{base_url}/{IMG_FILENAME}"
        result = post_to_instagram(image_url)
        return jsonify({"image_url": image_url, "status": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route(f"/{IMG_FILENAME}")
def serve_image():
    return send_file(IMG_FILENAME, mimetype='image/png')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
