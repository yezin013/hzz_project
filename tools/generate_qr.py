import qrcode
from PIL import Image
import os

# Configuration
DOMAIN = "https://hanzanzu.cloud"
LOGO_PATH = os.path.join("frontend", "public", "이리오너라.png")
OUTPUT_PATH = "hanzanzu_qr.png"

# Colors (Jumak Theme)
FILL_COLOR = "#2C3E50" # Dark Blue/Grey (Traditional looking)
BACK_COLOR = "white"

def create_qr():
    # 1. Create QR Code instance
    qr = qrcode.QRCode(
        version=None, # Auto-detect
        error_correction=qrcode.constants.ERROR_CORRECT_H, # High error correction for logo embedding
        box_size=10,
        border=4,
    )
    qr.add_data(DOMAIN)
    qr.make(fit=True)

    # 2. Generate Image
    img = qr.make_image(fill_color=FILL_COLOR, back_color=BACK_COLOR).convert('RGB')

    # 3. Add Logo
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH)
            
            # Resize logo
            # Calculate size: e.g., 20% of QR width
            qr_width, qr_height = img.size
            logo_size = int(qr_width * 0.2)
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Position logo at center
            pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
            img.paste(logo, pos, mask=logo if logo.mode == 'RGBA' else None)
            print(f"✅ Logo embedded: {LOGO_PATH}")
        except Exception as e:
            print(f"⚠️ Failed to add logo: {e}")
    else:
        print(f"⚠️ Logo not found at: {LOGO_PATH}")

    # 4. Save
    img.save(OUTPUT_PATH)
    print(f"🎉 QR Code saved to: {os.path.abspath(OUTPUT_PATH)}")

if __name__ == "__main__":
    create_qr()
