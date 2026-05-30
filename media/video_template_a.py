# media/video_template_a.py
# Template A — Slideshow style
# Multiple product images + Ken Burns zoom + voiceover + captions
# WHY MoviePy: free, local, no watermark, full control

from moviepy import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from PIL import Image
import numpy as np
import os

# Video settings
WIDTH, HEIGHT = 1920, 1080  # 1080p landscape (YouTube)
FPS = 24
SECONDS_PER_IMAGE = 6       # each image shows for 6 seconds

def load_and_resize(image_path: str) -> np.ndarray:
    """
    Crop and resize image to exactly 1920x1080.
    WHY crop-to-fill: every image fills the full frame equally,
    no black bars, consistent look across all images.
    """
    img = Image.open(image_path).convert("RGB")
    
    img_ratio = img.width / img.height
    target_ratio = WIDTH / HEIGHT  # 1920/1080 = 1.777
    
    if img_ratio > target_ratio:
        # Image too wide → crop sides
        new_width = int(img.height * target_ratio)
        x = (img.width - new_width) // 2
        img = img.crop((x, 0, x + new_width, img.height))
    else:
        # Image too tall → crop top/bottom
        new_height = int(img.width / target_ratio)
        y = (img.height - new_height) // 2
        img = img.crop((0, y, img.width, y + new_height))
    
    # Now resize to exact target size
    img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
    arr = np.array(img)
    # Force exact shape — prevents 1px rounding errors
    arr = arr[:HEIGHT, :WIDTH]
    return arr

def make_image_clip(image_path: str, duration: float) -> ImageClip:
    """
    Create video clip from image with Ken Burns zoom effect.
    """
    frame = load_and_resize(image_path)
    
    # Create base clip from numpy array directly
    clip = ImageClip(frame, duration=duration)
    
    # Ken Burns via resize effect over time
    clip = clip.resized(lambda t: 1.0 + (0.05 * t / duration))
    
    return clip

def make_caption_clip(text: str, duration: float) -> TextClip:
    text = text.replace("₹", "Rs.")
    
    clip = TextClip(
        text=text,
        font_size=44,
        color="white",
        stroke_color="black",
        stroke_width=2,
        size=(WIDTH - 200, 120),  # ← explicit height 120px, no auto-sizing
        method="caption"
    ).with_duration(duration).with_position(("center", HEIGHT - 160))
    
    return clip

def build_slideshow_video(
    image_paths: list,
    audio_path: str,
    captions: list,
    output_path: str,
    business_name: str = ""
) -> str:
    """
    Build full slideshow video.

    Args:
        image_paths: list of image file paths
        audio_path: path to voiceover MP3
        captions: list of caption strings (one per image)
        output_path: where to save final MP4
        business_name: shown as watermark

    Returns:
        path to output MP4
    """
    print(f"\n🎬 Building slideshow video...")
    print(f"   Images: {len(image_paths)}")
    print(f"   Audio: {audio_path}")

    # Load audio to get total duration
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration
    per_image = total_duration / len(image_paths)

    print(f"   Total duration: {total_duration:.1f}s")
    print(f"   Per image: {per_image:.1f}s")

    clips = []
    for i, img_path in enumerate(image_paths):
        print(f"   Processing image {i+1}/{len(image_paths)}: {img_path}")

        # Image with Ken Burns
        img_clip = make_image_clip(img_path, per_image)

        # Caption for this image
        if i < len(captions) and captions[i]:
            caption = make_caption_clip(captions[i], per_image)
            clip = CompositeVideoClip([img_clip, caption])
        else:
            clip = img_clip

        clips.append(clip)

    # Join all image clips
    final_video = concatenate_videoclips(clips)

    # Add voiceover
    final_video = final_video.with_audio(audio)

    # Save output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"\n⏳ Rendering video... (takes 1-2 minutes)")

    final_video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        logger="bar"
    )

    print(f"✅ Video saved: {output_path}")
    return output_path


if __name__ == "__main__":
    # Test with your orchid images
    result = build_slideshow_video(
        image_paths=[
            "inputs/images/Ord1.jpg",
            "inputs/images/Ord2.jpg",
            "inputs/images/Ord3.jpg"
        ],
        audio_path="outputs/audio/test_voiceover.mp3",
        captions=[
            "Rare Nagaland Orchids — Now in Kerala",
            "Exceptional Beauty, Hard to Find in India",
            "Order Now - Only ₹1450 | Jijo Orchid Nursery, Kollam"
        ],
        output_path="outputs/videos/test_slideshow.mp4",
        business_name="Jijo Orchid Nursery"
    )
    print(f"\n🎉 Open: {os.path.abspath(result)}") 
