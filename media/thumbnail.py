 # media/thumbnail.py
# Thumbnail generator using Pillow
# WHY: YouTube thumbnail = most important factor for click-through rate
# Output: 1280x720 JPG (YouTube standard)

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

THUMB_W, THUMB_H = 1280, 720

def create_thumbnail(
    image_path: str,
    product_name: str,
    price: str,
    business_name: str,
    output_path: str
) -> str:
    """
    Generate YouTube thumbnail.
    
    Layout:
    ┌─────────────────────────────┐
    │  [product image, full bg]   │
    │  dark gradient overlay      │
    │                             │
    │  PRODUCT NAME (large)       │
    │  Only Rs.XXXX               │
    │                             │
    │  [business name footer]     │
    └─────────────────────────────┘
    """
    print(f"\n🖼️ Generating thumbnail for: {product_name}")

    # ── Step 1: Load and crop image to 1280x720 ──────────────
    img = Image.open(image_path).convert("RGB")
    
    img_ratio = img.width / img.height
    target_ratio = THUMB_W / THUMB_H
    
    if img_ratio > target_ratio:
        new_width = int(img.height * target_ratio)
        x = (img.width - new_width) // 2
        img = img.crop((x, 0, x + new_width, img.height))
    else:
        new_height = int(img.width / target_ratio)
        y = (img.height - new_height) // 2
        img = img.crop((0, y, img.width, y + new_height))
    
    img = img.resize((THUMB_W, THUMB_H), Image.LANCZOS)

    # ── Step 2: Dark gradient overlay (bottom half) ───────────
    # WHY: makes white text readable over any image
    overlay = Image.new("RGBA", (THUMB_W, THUMB_H), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    for y in range(THUMB_H // 2, THUMB_H):
        alpha = int(180 * (y - THUMB_H // 2) / (THUMB_H // 2))
        draw_overlay.line([(0, y), (THUMB_W, y)], fill=(0, 0, 0, alpha))
    
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")

    draw = ImageDraw.Draw(img)

    # ── Step 3: Load fonts ────────────────────────────────────
    # WHY try/except: system fonts vary — fallback to default if not found
    try:
        font_large = ImageFont.truetype("arial.ttf", 80)
        font_medium = ImageFont.truetype("arial.ttf", 60)
        font_small = ImageFont.truetype("arial.ttf", 36)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # ── Step 4: Product name (large, white) ───────────────────
    draw.text(
        (60, THUMB_H - 250),
        product_name.upper(),
        font=font_medium,
        fill="white",
        stroke_width=2,
        stroke_fill="black"
    )

    # ── Step 5: Price badge (gold) ────────────────────────────
    price_text = f"Only Rs.{price}"
    draw.text(
        (60, THUMB_H - 170),
        price_text,
        font=font_medium,
        fill="#FFD700",
        stroke_width=2,
        stroke_fill="black"
    )

    # ── Step 6: Business name footer (small, white) ───────────
    draw.text(
        (60, THUMB_H - 85),
        business_name,
        font=font_small,
        fill="white",
        stroke_width=2,
        stroke_fill="black"
    )

    # ── Step 7: Price badge box (top right) ───────────────────
    # badge_x, badge_y = THUMB_W - 320, 30
    # draw.rectangle(
    #     [badge_x, badge_y, badge_x + 280, badge_y + 80],
    #     fill="#FF4444",
    #     outline="white",
    #     width=3
    # )
    # draw.text(
    #     (badge_x + 20, badge_y + 10),
    #     f"Rs.{price}",
    #     font=font_medium,
    #     fill="white"
    # )

    # ── Save ──────────────────────────────────────────────────
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "JPEG", quality=95)
    print(f"✅ Thumbnail saved: {output_path}")
    return output_path


if __name__ == "__main__":
    result = create_thumbnail(
        image_path="inputs/images/Ord1.jpg",
        product_name="Fancy Orchid",
        price="1450",
        business_name="Jijo Orchid Nursery, Kollam",
        output_path="outputs/thumbnails/test_thumbnail.jpg"
    )
    print(f"\n🎉 Open: {os.path.abspath(result)}")
