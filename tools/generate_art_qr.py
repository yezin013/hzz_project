from amzqr import amzqr
from PIL import Image, ImageSequence
import os

# Configuration
DOMAIN = "https://hanzanzu.cloud"
OUTPUT_DIR = os.getcwd()

# 1. Background Image QR (Artistic)
# You need a background image (PNG/JPG)
# Example: Using '이리오너라.png'
BG_IMAGE = os.path.join("움짤.gif")
OUTPUT_ART = "hanzanzu_art_qr.png"

# 2. Animated QR (GIF)
# You need a GIF file.
# Example: If you have a 'cheers.gif' in current folder, change this path.
# BG_GIF = "cheers.gif" 
BG_GIF = None # Set this to your gif path if you have one!
OUTPUT_GIF = "hanzanzu_ani_qr.gif"

def create_artistic_qr():
    print(f"🎨 Generating Artistic QR for {DOMAIN}...")
    
    # Check if background image exists
    if os.path.exists(BG_IMAGE):
        print(f"   Using background: {BG_IMAGE}")
        
        # Auto-correct output extension if input is GIF
        save_name = OUTPUT_ART
        if BG_IMAGE.lower().endswith('.gif') and not save_name.lower().endswith('.gif'):
            save_name = save_name.rsplit('.', 1)[0] + '.gif'
            print(f"   ℹ️ Detected GIF input, changing output to: {save_name}")

        version, level, qr_name = amzqr.run(
            words=DOMAIN,
            version=1,
            level='H',
            picture=BG_IMAGE,
            colorized=True,
            contrast=1.0,
            brightness=1.0,
            save_name=save_name,
            save_dir=OUTPUT_DIR
        )
        print(f"   ✅ Saved to: {qr_name}")

        # Post-process: Fix infinite loop if output is GIF
        if save_name.lower().endswith('.gif'):
            try:
                full_path = os.path.join(OUTPUT_DIR, save_name)
                img = Image.open(full_path)
                
                # Get all frames
                frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
                if frames:
                    # Save with loop=0 (infinite)
                    frames[0].save(
                        full_path,
                        save_all=True,
                        append_images=frames[1:],
                        loop=0,
                        duration=img.info.get('duration', 100),
                        disposal=2 # Restore background to prevent glitches
                    )
                    print("   🔄 Applied infinite loop fix to GIF.")
            except Exception as e:
                print(f"   ⚠️ Loop fix failed: {e}")

    else:
        print(f"   ⚠️ Background image not found: {BG_IMAGE}")

def create_animated_qr():
    if BG_GIF and os.path.exists(BG_GIF):
        print(f"🎬 Generating Animated QR for {DOMAIN}...")
        version, level, qr_name = amzqr.run(
            words=DOMAIN,
            version=1,
            level='H',
            picture=BG_GIF,
            colorized=True,
            contrast=1.0,
            brightness=1.0,
            save_name=OUTPUT_GIF,
            save_dir=OUTPUT_DIR
        )
        print(f"   ✅ Saved to: {qr_name}")
    elif BG_GIF:
        print(f"   ⚠️ GIF file not found: {BG_GIF}")

if __name__ == "__main__":
    create_artistic_qr()
    create_animated_qr()
    
    print("\n[Tip] 움직이는 QR을 만드려면:")
    print("1. 원하는 GIF 파일(예: 술따르는 장면)을 구해서 소스 폴더에 넣으세요.")
    print("2. 이 스크립트(tools/generate_art_qr.py)의 BG_GIF 변수를 파일명으로 수정하세요.")
    print("3. 다시 실행하면 움직이는 QR이 나옵니다! ✨")
