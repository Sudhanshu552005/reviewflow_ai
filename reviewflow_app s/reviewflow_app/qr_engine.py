import qrcode
from PIL import Image, ImageDraw
import os

def generate_beautified_qr(business_id, business_name, category, custom_category=None):

    themes = {
        "Restaurant": {"bg": (194, 65, 12), "accent": (67, 20, 7), "tagline": "Rate Your Dining Experience!"},
        "Automobile": {"bg": (51, 65, 85), "accent": (249, 115, 22), "tagline": "Rate Our Mechanical Service!"},
        "Retail": {"bg": (244, 114, 182), "accent": (30, 41, 59), "tagline": "Rate Your Fashion Experience!"},
        "Salon": {"bg": (167, 139, 250), "accent": (124, 45, 18), "tagline": "Rate Your Relaxation Spa!"},
        "Hospitality": {"bg": (23, 37, 84), "accent": (234, 179, 8), "tagline": "Rate Your Premium Stay!"}
    }

    theme = themes.get(
        category,
        {"bg": (79, 70, 229), "accent": (49, 46, 129), "tagline": "We Value Your Feedback!"}
    )

    display_category = custom_category if custom_category else category

    # Canvas
    card_width = 400
    card_height = 550
    card = Image.new("RGB", (card_width, card_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(card)

    # Header
    draw.rectangle([0, 0, card_width, 110], fill=theme["bg"])

    # ✅ IMPORTANT: production-safe URL
   customer_facing_url = f"https://reviewflow-apps.onrender.com/review/{business_id}"

    # ✅ FIXED QR SETTINGS (THIS IS THE MAIN FIX)
    qr = qrcode.QRCode(
        version=None,  # auto size (VERY IMPORTANT)
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4  # MUST NOT be 0
    )

    qr.add_data(customer_facing_url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # No distortion risk
    qr_img = qr_img.resize((260, 260))

    # Place QR
    card.paste(qr_img, ((card_width - 260) // 2, 165))

    # Text
    draw.text(
        (card_width // 2, 35),
        business_name.upper(),
        fill=(255, 255, 255),
        anchor="mm"
    )

    draw.text(
        (card_width // 2, 70),
        "SCAN TO SHARE FEEDBACK",
        fill=(255, 255, 255),
        anchor="mm"
    )

    # Footer
    draw.rectangle([0, card_height - 90, card_width, card_height], fill=(248, 250, 252))

    draw.text(
        (card_width // 2, card_height - 60),
        theme["tagline"],
        fill=theme["accent"],
        anchor="mm"
    )

    draw.text(
        (card_width // 2, card_height - 30),
        f"Powered by ReviewFlow AI • {display_category}",
        fill=(148, 163, 184),
        anchor="mm"
    )

    # Save
    os.makedirs("static/qr_codes", exist_ok=True)
    output_filename = f"static/qr_codes/tenant_{business_id}.png"
    card.save(output_filename, "PNG")

    return output_filename
