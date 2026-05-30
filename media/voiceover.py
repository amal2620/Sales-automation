# media/voiceover.py
# Generates voiceover using Microsoft Edge TTS
# Free, no API key, Python 3.12 compatible, Malayalam support

import os
import asyncio
import edge_tts
from dotenv import load_dotenv

load_dotenv()

# Malayalam voice options:
# ml-IN-MidhunNeural    ← male Malayalam voice
# ml-IN-SobhanaNeural   ← female Malayalam voice
MALAYALAM_VOICE = "ml-IN-SobhanaNeural"
ENGLISH_VOICE   = "en-IN-NeerjaNeural"

async def _generate_audio(text: str, voice: str, output_path: str):
    """Internal async function — edge-tts requires async"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def generate_voiceover(
    text: str,
    output_path: str,
    language: str = "Malayalam"
) -> str:
    """
    Generate voiceover from text using Edge TTS.

    Args:
        text: text to speak
        output_path: where to save .mp3 file
        language: "Malayalam" or "English"

    Returns:
        path to audio file
    """
    voice = MALAYALAM_VOICE if language == "Malayalam" else ENGLISH_VOICE

    print(f"\n🎙️ Generating {language} voiceover...")
    print(f"   Voice: {voice}")
    print(f"   Text: {text[:60]}...")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        # Run async function
        asyncio.run(_generate_audio(text, voice, output_path))
        print(f"✅ Voiceover saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Voiceover failed: {e}")
        return None


if __name__ == "__main__":
    # Test Malayalam voiceover
    test_text = "കൊല്ലത്തെ ജിജോ ഓർക്കിഡ് നഴ്സറിയിലേക്ക് സ്വാഗതം. വെറും 1450 രൂപയ്ക്ക് ഇപ്പോൾ ഓർഡർ ചെയ്യുക!"

    result = generate_voiceover(
        text=test_text,
        output_path="outputs/audio/test_voiceover.mp3",
        language="Malayalam"
    )

    if result:
        print(f"\n✅ Open this file to listen:")
        print(f"   {os.path.abspath(result)}")
