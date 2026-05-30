 # media/video_template_b.py
# Template B — Hero Image style
# Single strong product image + animated text overlays + voiceover
# WHY different from A: cleaner, modern look, text tells the story

from moviepy import ImageClip, AudioFileClip, TextClip, CompositeVideoClip
from PIL import Image
import numpy as np
import os

WIDTH, HEIGHT = 1920, 1080
FPS = 24

def load_and_crop(image_path: str) -> np.ndarray:
    """Same crop-to-fill logic as Template A"""
    img = Image.open(image_path).convert("RGB")
    img_ratio = img.width / img.height
    target_ratio = WIDTH / HEIGHT

    if img_ratio > target_ratio:
        new_width = int(img.height * target_ratio)
        x = (img.width - new_width) // 2
        img = img.crop((x, 0, x + new_width, img.height))
    else:
        new_height = int(img.width / target_ratio)
        y = (img.height - new_height) // 2
        img = img.crop((0, y, img.width, y + new_height))

    img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
    return np.array(img)

def make_text_overlay(text: str, fontsize: int, color: str,
                      position: tuple, duration: float,
                      start_time: float = 0) -> TextClip:
    """
    Create text overlay that appears at specific time.
    WHY timed text: text appears as voiceover mentions each point
    """
    return (TextClip(
        text=text,
        font_size=fontsize,
        color=color,
        stroke_color="black",
        stroke_width=2,
        size=(WIDTH - 200, None),
        method="caption"
    )
    .with_duration(duration - start_time)
    .with_start(start_time)
    .with_position(position))

def build_hero_video(
    image_path: str,
    audio_path: str,
    product_name: str,
    price: str,
    hook_text: str,
    cta_text: str,
    business_name: str,
    output_path: str
) -> str:
    """
    Build hero image video with timed text overlays.

    Args:
        image_path: single hero product image
        audio_path: voiceover MP3
        product_name: shown as title
        price: shown as price badge
        hook_text: appears at start
        cta_text: appears near end
        business_name: watermark
        output_path: where to save MP4
    """
    print(f"\n🎬 Building hero video for: {product_name}")

    audio = AudioFileClip(audio_path)
    duration = audio.duration

    # Base — hero image full duration with slow Ken Burns
    frame = load_and_crop(image_path)
    base = ImageClip(frame, duration=duration)
    base = base.resized(lambda t: 1.0 + (0.03 * t / duration))  # slow zoom in

    # Dark overlay — makes text readable over image
    # WHY: text on bright image = unreadable
    overlay_frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    dark_overlay = (ImageClip(overlay_frame, duration=duration)
                   .with_opacity(0.45))

    # Text layers — appear at different times
    # Product name — appears at 0s
    title = make_text_overlay(
        text=product_name,
        fontsize=72,
        color="white",
        position=("center", 200),
        duration=duration,
        start_time=0
    )

    # Price badge — appears at 1s
    price_text = make_text_overlay(
        text=f"Only ₹{price}",
        fontsize=60,
        color="#FFD700",  # gold color
        position=("center", 320),
        duration=duration,
        start_time=1
    )

    # Hook text — appears at 2s
    hook = make_text_overlay(
        text=hook_text,
        fontsize=44,
        color="white",
        position=("center", 500),
        duration=duration,
        start_time=2
    )

    # CTA — appears at 75% of video duration
    cta_start = duration * 0.75
    cta = make_text_overlay(
        text=cta_text,
        fontsize=48,
        color="#00FF88",  # green
        position=("center", HEIGHT - 200),
        duration=duration,
        start_time=cta_start
    )

    # Business name watermark — full duration, top right
    watermark = make_text_overlay(
        text=business_name,
        fontsize=32,
        color="white",
        position=(WIDTH - 500, 40),
        duration=duration,
        start_time=0
    )

    # Composite all layers
    final = CompositeVideoClip([
        base,
        dark_overlay,
        title,
        price_text,
        hook,
        cta,
        watermark
    ]).with_audio(audio)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print("⏳ Rendering... (1-2 minutes)")

    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        logger="bar"
    )

    print(f"✅ Hero video saved: {output_path}")
    return output_path


if __name__ == "__main__":
    result = build_hero_video(
        image_path="inputs/images/Ord1.jpg",
        audio_path="outputs/audio/test_voiceover.mp3",
        product_name="Fancy Orchid",
        price="1450",
        hook_text="Rare imported orchid from Nagaland — now in Kerala",
        cta_text="Order now at Jijo Orchid Nursery, Kollam",
        business_name="Jijo Orchid Nursery",
        output_path="outputs/videos/test_hero.mp4"
    )
    print(f"\n🎉 Open: {os.path.abspath(result)}")
