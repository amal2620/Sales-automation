# tools/translation.py
# Translation Tool — English → Malayalam/Tamil/Hindi
# Uses Facebook NLLB-200 — no token, no Rust, works immediately

import os
import json
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "facebook/nllb-200-distilled-600M"

LANG_CODES = {
    "Malayalam": "mal_Mlym",
    "Tamil":     "tam_Taml",
    "Hindi":     "hin_Deva",
    "Telugu":    "tel_Telu",
    "Kannada":   "kan_Knda"
}

tokenizer = None
model = None

def load_model():
    global tokenizer, model
    if model is None:
        try:
            print("🔄 Loading NLLB-200 model... (~2 mins first time)")
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
            if torch.cuda.is_available():
                model = model.cuda()
                print("✅ NLLB-200 loaded on GPU")
            else:
                print("✅ NLLB-200 loaded on CPU")
        except Exception as e:
            print(f"❌ Model load failed: {e}")
            return False
    return True

def translate_text(text: str, target_language: str = "Malayalam") -> str:
    if target_language not in LANG_CODES:
        return text
    if not load_model():
        return f"[Translation failed] {text}"
    try:
        tgt_lang = LANG_CODES[target_language]
        inputs = tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        )
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        target_lang_id = tokenizer.convert_tokens_to_ids(tgt_lang)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                forced_bos_token_id=target_lang_id,
                num_beams=4,
                max_length=512
            )
        return tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
    except Exception as e:
        print(f"⚠️ Translation error: {e}")
        return text

def translate_script(script: dict, target_language: str = "Malayalam") -> dict:
    print(f"\n🌐 Translating script to {target_language}...")
    translated = {
        "title":            translate_text(script.get("title", ""), target_language),
        "hook":             translate_text(script.get("hook", ""), target_language),
        "body":             translate_text(script.get("body", ""), target_language),
        "cta":              translate_text(script.get("cta", ""), target_language),
        "description":      script.get("description", ""),  # English for SEO
        "tags":             script.get("tags", []),          # English for SEO
        "language":         target_language,
        "original_english": script
    }
    print(f"✅ Translation to {target_language} complete!")
    return translated

if __name__ == "__main__":
    test_script = {
        "title": "Rare Fancy Orchid Kollam | Exotic Plants Kerala",
        "hook": "STOP scrolling! Are you looking for the most exotic rare beauty in Kerala?",
        "body": "Welcome to Jijo Orchid Nursery in Kollam. This rare orchid is imported from Nagaland.",
        "cta": "Order now for just ₹1450. Limited stock available!",
        "description": "Buy rare exotic orchids in Kollam Kerala...",
        "tags": ["Fancy Orchid Kollam", "exotic plants Kerala"]
    }
    result = translate_script(test_script, "Malayalam")
    print("\n" + "="*50)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    