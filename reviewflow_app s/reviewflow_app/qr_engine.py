import os

import qrcode
from PIL import Image, ImageDraw


PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://reviewflow-apps.onrender.com").rstrip("/")
QR_CODE_DIR = os.getenv("QR_CODE_DIR", "static/qr_codes")


def generate_beautified_qr(business_id, business_name, category, custom_category=None):
    themes = {
        "Restaurant": {"bg": (194, 65, 12), "accent": (67, 20, 7), "tagline": "Rate Your Dining Experience!"},
        "Automobile": {"bg": (51, 65, 85), "accent": (249, 115, 22), "tagline": "Rate Our Mechanical Service!"},
        "Retail": {"bg": (244, 114, 182), "accent": (30, 41, 59), "tagline": "Rate Your Fashion Experience!"},
        "Salon": {"bg": (167, 139, 250), "accent": (124, 45, 18), "tagline": "Rate Your Relaxation Spa!"},
        "Hospitality": {"bg": (23, 37, 84), "accent": (234, 179, 8), "tagline": "Rate Your Premium Stay!"},
    }

    theme = themes.get(
        category,
        {"bg": (79, 70, 229), "accent": (49, 46, 129), "tagline": "We Value Your Feedback!"},
    )
    display_category = custom_category if custom_category else category

    card_width = 400
    card_height = 550
    card = Image.new("RGB", (card_width, card_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(card)

    draw.rectangle([0, 0, card_width, 110], fill=theme["bg"])

    customer_facing_url = f"{PUBLIC_BASE_URL}/review/{business_id}"
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(customer_facing_url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img = qr_img.resize((260, 260))
    card.paste(qr_img, ((card_width - 260) // 2, 165))

    draw.text((card_width // 2, 35), business_name.upper(), fill=(255, 255, 255), anchor="mm")
    draw.text((card_width // 2, 70), "SCAN TO SHARE FEEDBACK", fill=(255, 255, 255), anchor="mm")

    draw.rectangle([0, card_height - 90, card_width, card_height], fill=(248, 250, 252))
    draw.text((card_width // 2, card_height - 60), theme["tagline"], fill=theme["accent"], anchor="mm")
    draw.text(
        (card_width // 2, card_height - 30),
        f"Powered by ReviewFlow AI - {display_category}",
        fill=(148, 163, 184),
        anchor="mm",
    )

    os.makedirs(QR_CODE_DIR, exist_ok=True)
    output_filename = os.path.join(QR_CODE_DIR, f"tenant_{business_id}.png")
    card.save(output_filename, "PNG")
    return output_filename
