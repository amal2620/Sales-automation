# dashboard/frontend/app.py
# VyaparAI — FastAPI Dashboard
# Handles: product input, pipeline streaming, video preview, approve/reject

import os, time, threading, queue, json
from datetime import datetime
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from werkzeug.utils import secure_filename
import uvicorn
import sys

# Add project root to path so we can import agents
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

app = FastAPI(title="VyaparAI Dashboard")

# Static files + templates
app.mount("/static", StaticFiles(directory="dashboard/frontend/static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
templates = Jinja2Templates(directory="dashboard/frontend/templates")

ALLOWED = {'png', 'jpg', 'jpeg', 'webp'}
UPLOAD_DIR = "inputs/images"

# Global state
_event_queue: queue.Queue = queue.Queue()
_pipeline_state = {
    "status": "idle",
    "video_path": None,
    "thumbnail_path": None,
    "script": None,
    "product_name": None,
    "approved": None
}

# ── SSE helpers ───────────────────────────────────────────────
def push(msg, level='info', step=None, progress=None):
    payload = {
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'message': msg,
        'level': level,
        'step': step,
        'progress': progress,
    }
    _event_queue.put({'type': 'log', 'data': payload})
    time.sleep(0.05)

def push_step(index, status):
    _event_queue.put({'type': 'step_update', 'data': {'index': index, 'status': status}})
    time.sleep(0.08)

def push_ready(video_path, thumbnail_path, script):
    """Tell frontend pipeline is done — show preview"""
    _event_queue.put({
        'type': 'pipeline_ready',
        'data': {
            'video_path': video_path,
            'thumbnail_path': thumbnail_path,
            'script': script
        }
    })

_STOP = object()

# ── Routes ────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/stream")
async def stream():
    """SSE endpoint — browser subscribes for live pipeline updates"""
    def generate():
        while True:
            item = _event_queue.get()
            yield f"data: {json.dumps(item)}\n\n"
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

@app.post("/generate")
async def generate(
    business_name: str = Form(...),
    product_name: str = Form(...),
    price: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    language: str = Form("Malayalam"),
    images: list[UploadFile] = File(None)
):
    # Save uploaded image
    # NEW multiple image save
    image_paths = []
    if images:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        for image in images:
            if image and image.filename:
                ext = image.filename.rsplit('.', 1)[-1].lower()
                if ext in ALLOWED:
                    filename = secure_filename(image.filename)
                    path = os.path.join(UPLOAD_DIR, filename)
                    with open(path, "wb") as f:
                        f.write(await image.read())
                    image_paths.append(path)

    # Update global state
    _pipeline_state["status"] = "running"
    _pipeline_state["product_name"] = product_name
    _pipeline_state["approved"] = None
    _pipeline_state["business_name"] = business_name
    _pipeline_state["price"] = price
    _pipeline_state["description"] = description
    _pipeline_state["location"] = location
    _pipeline_state["language"] = language
    _pipeline_state["image_paths"] = image_paths

    # Run pipeline in background thread
    t = threading.Thread(
        target=run_pipeline,
        args=(business_name, product_name, price, description, location, language, image_paths),
        daemon=True
    )
    t.start()

    return JSONResponse({'success': True, 'message': 'Pipeline started'})

@app.post("/approve")
async def approve():
    """Owner approves video — trigger publishing"""
    _pipeline_state["approved"] = True
    _pipeline_state["status"] = "approved"
    push("✅ Owner approved — starting publishing...", 'success', step=8)
    # TODO Phase 8: call publishing agent here
    return JSONResponse({'success': True, 'message': 'Approved'})

@app.post("/reject")
async def reject(feedback: str = Form("")):
    _pipeline_state["approved"] = False
    _pipeline_state["status"] = "rejected"
    push(f"❌ Rejected — feedback: {feedback}", 'warn', step=8)
    push("🔄 Re-running pipeline with feedback...", 'info')

    # Re-run pipeline in background with feedback appended to description
    state = _pipeline_state
    t = threading.Thread(
        target=run_pipeline,
        args=(
            state.get("business_name", ""),
            state.get("product_name", ""),
            state.get("price", ""),
            state.get("description", "") + f". Owner feedback: {feedback}",
            state.get("location", ""),
            state.get("language", "Malayalam"),
            state.get("image_paths", [])
        ),
        daemon=True
    )
    t.start()
    return JSONResponse({'success': True, 'message': 'Rejected — rerunning'})

# ── Real pipeline ─────────────────────────────────────────────
def run_pipeline(business_name, product_name, price, description, location, language, image_paths):
    try:
        from agents.supervisor_agent import run_pipeline as run_supervisor
        from media.voiceover import generate_voiceover
        from media.video_template_a import build_slideshow_video
        from media.thumbnail import create_thumbnail

        # Step 1 — Input
        push_step(0, 'active')
        push(f"✦ Product: {product_name} | Price: Rs.{price}", 'info', step=1, progress=5)
        push(f"✦ Location: {location} | Language: {language}", 'info', step=1, progress=10)
        push("✔ Input validated", 'success', step=1, progress=15)
        push_step(0, 'completed')

        # Step 2 — Trend + Script via Supervisor
        push_step(1, 'active')
        push("⟳ Running Trend Agent...", 'info', step=2, progress=20)
        push_step(1, 'completed')

        push_step(2, 'active')
        push("⟳ Running Script Agent + Critic loop...", 'info', step=3, progress=35)

        result = run_supervisor(
        business_name=business_name,
        product_name=product_name,
        price=price,
        description=description,
        location=location,
        product_category="general",
        language=language
        )

        script = result.get("script", {})
        push(f"✔ Script approved — {script.get('title', '')}", 'success', step=3, progress=50)
        push_step(2, 'completed')

        # Step 3 — Translation
        push_step(3, 'active')
        push("⟳ Translating to Malayalam...", 'info', step=4, progress=55)
        translated = result.get("translated", {})
        push("✔ Translation complete", 'success', step=4, progress=60)
        push_step(3, 'completed')

        # Step 4 — Voiceover
        push_step(4, 'active')
        push("⟳ Generating Malayalam voiceover...", 'info', step=5, progress=65)

        # unwrap nested script
        actual_script = script.get("script", script)
        voiceover_text = actual_script.get(
            "body",
            f"Welcome to {business_name}. {product_name} available for Rs.{price}"
        )
        audio_path = f"outputs/audio/{product_name.replace(' ', '_')}_voiceover.mp3"
        generate_voiceover(voiceover_text, audio_path, language)
        push("✔ Voiceover generated", 'success', step=5, progress=70)
        push_step(4, 'completed')

        # Step 5 — Video
        push_step(5, 'active')
        push("⟳ Assembling video...", 'info', step=6, progress=75)

        # use actual script for captions
        captions = [
            actual_script.get("hook", product_name)[:100],
            actual_script.get("body", "")[:80],
            f"Only Rs.{price} — {business_name}"
        ]

        # use ALL valid images
        valid_images = [
            p for p in image_paths
            if p.lower().endswith(('.jpg', '.jpeg', '.png'))
        ]
        if not valid_images:
            valid_images = [
                os.path.join(UPLOAD_DIR, f)
                for f in os.listdir(UPLOAD_DIR)
                if f.lower().endswith(('.jpg', '.jpeg', '.png'))
            ]

        video_path = f"outputs/videos/{product_name.replace(' ', '_')}_video.mp4"
        build_slideshow_video(valid_images, audio_path, captions, video_path, business_name)
        push("✔ Video assembled", 'success', step=6, progress=85)
        push_step(5, 'completed')

        # Step 6 — Thumbnail
        push_step(6, 'active')
        push("⟳ Generating thumbnail...", 'info', step=7, progress=88)
        thumb_path = f"outputs/thumbnails/{product_name.replace(' ', '_')}_thumb.jpg"
        create_thumbnail(image_paths[0], product_name, price, business_name, thumb_path)
        push("✔ Thumbnail generated", 'success', step=7, progress=92)
        push_step(6, 'completed')

        # Step 7 — Ready for approval
        push_step(7, 'active')
        push("✅ Pipeline complete — awaiting your approval", 'success', step=8, progress=100)

        _pipeline_state["video_path"] = video_path
        _pipeline_state["thumbnail_path"] = thumb_path
        _pipeline_state["script"] = script
        _pipeline_state["status"] = "awaiting_approval"

        push_ready(video_path, thumb_path, script)
        push_step(7, 'completed')

    except Exception as e:
        push(f"❌ Pipeline error: {str(e)}", 'error')
        _pipeline_state["status"] = "error"

    # DON'T send _STOP — keep stream alive for reject reruns
    # Only send completion signal
    _event_queue.put({'type': 'pipeline_done', 'data': {}})


if __name__ == "__main__":
    os.makedirs("outputs/videos", exist_ok=True)
    os.makedirs("outputs/audio", exist_ok=True)
    os.makedirs("outputs/thumbnails", exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)