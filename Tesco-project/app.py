import streamlit as st
import cohere
from PIL import Image, ImageDraw, ImageFont
import io
import os

# ================= CONFIG =================
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
if not COHERE_API_KEY:
    st.error("COHERE_API_KEY not set in environment")
    st.stop()

co = cohere.Client(COHERE_API_KEY)

TESCO_RULES = {
    "safe_zone": 20,
    "cta_max_words": 3,
    "drinkaware_required": True
}

BANNER_SIZE = (300, 250)

# ================= UI STYLES =================
st.markdown("""
<style>
body {
    background-color: #f4f6f8;
}
.block-container {
    padding-top: 2rem;
}
.card {
    background-color: white;
    padding: 1.5rem;
    border-radius: 14px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    margin-bottom: 1.5rem;
}
.section-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
}
.badge-success {
    background-color: #d4edda;
    color: #155724;
    padding: 6px 14px;
    border-radius: 20px;
    display: inline-block;
    margin-bottom: 8px;
    font-weight: 600;
}
.badge-error {
    background-color: #f8d7da;
    color: #721c24;
    padding: 6px 14px;
    border-radius: 20px;
    display: inline-block;
    margin-bottom: 8px;
    font-weight: 600;
}
button[kind="primary"] {
    background-color: #00539f !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# ================= RULE ENGINE =================
def validate_copy(copy_text):
    violations = []
    if len(copy_text.split()) > 6:
        violations.append("Headline exceeds 6 words (Tesco guideline)")
    return violations

def validate_layout(elements):
    violations = []
    for name, (x, y, w, h) in elements.items():
        if x < TESCO_RULES["safe_zone"] or y < TESCO_RULES["safe_zone"]:
            violations.append(f"{name} violates safe zone")
    return violations

# ================= TEXT WRAP =================
def draw_wrapped_text(draw, text, font, x, y, max_width, line_spacing=4):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]

        if text_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    for i, line in enumerate(lines[:2]):  # Tesco-safe: max 2 lines
        draw.text(
            (x, y + i * (font.size + line_spacing)),
            line,
            fill="black",
            font=font
        )

# ================= COHERE COPY =================
def rewrite_copy(user_copy):
    prompt = f"""
You are a Tesco advertising copy assistant.

Rewrite the text below so it:
- Has MAX 6 words
- Uses friendly grocery tone
- Avoids exaggeration
- Is suitable for Tesco retail ads

Text:
{user_copy}
"""

    response = co.chat(
        model="command-a-03-2025",
        message=prompt,
        temperature=0.3,
    )

    return response.text.strip()

# ================= BANNER =================
def generate_banner(packshot_img, headline):
    canvas = Image.new("RGB", BANNER_SIZE, "#ffffff")
    draw = ImageDraw.Draw(canvas)

    # Packshot
    packshot = packshot_img.resize((120, 120))
    canvas.paste(packshot, (20, 80))

    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()

    # Headline
    draw_wrapped_text(
        draw,
        headline,
        font,
        x=160,
        y=50,
        max_width=120
    )

    # CTA
    draw.rounded_rectangle([160, 120, 260, 150], radius=6, fill="#00539f")
    draw.text((178, 128), "Shop now", fill="white", font=font)

    # Drinkaware
    draw.text((20, 215), "Drinkaware.co.uk", fill="black", font=font)

    elements = {
        "Packshot": (20, 80, 120, 120),
        "Headline": (160, 50, 120, 40),
        "CTA": (160, 120, 100, 30),
        "Drinkaware": (20, 215, 120, 20)
    }

    return canvas, elements

# ================= APP =================
st.set_page_config(page_title="Tesco GenAI Creative Builder", layout="centered")

st.title("🛒 Tesco GenAI Creative Builder")
st.caption("Automatically generate Tesco-compliant marketing banners")

# -------- Upload --------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">1️⃣ Upload Packshot</div>', unsafe_allow_html=True)

packshot_file = st.file_uploader(
    "Product image",
    type=["png", "jpg", "jpeg"],
    help="Clear product image on white or transparent background"
)

if packshot_file:
    st.image(packshot_file, width=160, caption="Packshot preview")

st.markdown('</div>', unsafe_allow_html=True)

# -------- Copy --------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">2️⃣ Enter Headline</div>', unsafe_allow_html=True)

user_copy = st.text_input(
    "Marketing headline",
    max_chars=40,
    help="Will be rewritten to Tesco-safe 6 words"
)

if user_copy:
    st.caption(f"Words entered: {len(user_copy.split())}")

st.markdown('</div>', unsafe_allow_html=True)

# -------- Generate --------
generate = st.button("✨ Generate Tesco Banner", type="primary")

if generate:
    if not packshot_file or not user_copy:
        st.error("Please upload a packshot and enter copy")
    else:
        packshot_img = Image.open(packshot_file).convert("RGBA")

        with st.spinner("Generating Tesco-compliant copy..."):
            rewritten_copy = rewrite_copy(user_copy)

        banner, layout_elements = generate_banner(packshot_img, rewritten_copy)

        copy_issues = validate_copy(rewritten_copy)
        layout_issues = validate_layout(layout_elements)

        # Banner
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">3️⃣ Generated Banner</div>', unsafe_allow_html=True)
        st.image(banner)
        st.markdown('</div>', unsafe_allow_html=True)

        # Compliance
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">4️⃣ Compliance Report</div>', unsafe_allow_html=True)

        if not copy_issues and not layout_issues:
            st.markdown('<div class="badge-success">✔ Fully Tesco Compliant</div>', unsafe_allow_html=True)
        else:
            for issue in copy_issues + layout_issues:
                st.markdown(f'<div class="badge-error">⚠ {issue}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Final Copy
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Final Copy Used</div>', unsafe_allow_html=True)
        st.code(rewritten_copy)
        st.markdown('</div>', unsafe_allow_html=True)

        # Download
        img_bytes = io.BytesIO()
        banner.save(img_bytes, format="PNG")
        st.download_button(
            "⬇ Download Banner",
            img_bytes.getvalue(),
            "tesco_banner.png",
            "image/png"
        )
