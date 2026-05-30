"""
YouTube Automation System — Flask Backend (SSE edition)
Uses Server-Sent Events instead of SocketIO for zero-extra-dep real-time streaming.
Compatible with: pip install flask werkzeug
"""

import os, time, random, threading, queue, json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from werkzeug.utils import secure_filename

# ─── Config ───────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY']       = 'yt-automation-secret-2024'
app.config['UPLOAD_FOLDER']    = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Global queue that the SSE stream drains
_event_queue: queue.Queue = queue.Queue()

def allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED

# ─── SSE Helpers ──────────────────────────────────────────────────────────────
def push(msg, level='info', step=None, progress=None):
    payload = {
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'message':   msg,
        'level':     level,
        'step':      step,
        'progress':  progress,
    }
    _event_queue.put({'type': 'log', 'data': payload})
    time.sleep(0.05)

def push_step(index, status):
    _event_queue.put({'type': 'step_update', 'data': {'index': index, 'status': status}})
    time.sleep(0.08)

def push_done(vid_id):
    _event_queue.put({'type': 'pipeline_complete', 'data': {'success': True, 'video_id': vid_id}})

# Sentinel to end stream
_STOP = object()

# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/stream')
def stream():
    """SSE endpoint — browser subscribes here for live events."""
    def generate():
        while True:
            item = _event_queue.get()
            if item is _STOP:
                break
            yield f"data: {json.dumps(item)}\n\n"
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )


@app.route('/generate', methods=['POST'])
def generate():
    topic      = request.form.get('topic', '').strip()
    description= request.form.get('description', '').strip()
    keywords_r = request.form.get('keywords', '')
    keywords   = [k.strip() for k in keywords_r.split(',') if k.strip()]

    if not topic:
        return jsonify({'success': False, 'error': 'Topic is required'}), 400

    image_path = None
    if 'image' in request.files:
        f = request.files['image']
        if f and f.filename and allowed(f.filename):
            fn  = secure_filename(f.filename)
            dir_ = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
            os.makedirs(dir_, exist_ok=True)
            image_path = os.path.join(dir_, fn)
            f.save(image_path)

    t = threading.Thread(
        target=run_pipeline,
        args=(topic, description, keywords, image_path),
        daemon=True,
    )
    t.start()
    return jsonify({'success': True, 'message': 'Pipeline started'})


# ─── Simulated Pipeline ───────────────────────────────────────────────────────
TRENDING = [
    "Best Running Shoes 2024", "Nike Air Max vs Adidas Ultraboost",
    "Top 10 Budget Sneakers", "Sneaker Care Tips for Beginners",
    "Limited Edition Drops This Week",
]
SEO_KW = ["buy","review","best","top rated","affordable","2024","unboxing","comparison","honest review","worth it"]


def run_pipeline(topic, description, keywords, image_path):
    # ── Step 1 ────────────────────────────────────────────────────────────────
    push_step(0, 'active')
    push("═══════════════════════════════════════", 'system', step=1)
    push("  STEP 1 — INPUT TRIGGER", 'system', step=1)
    push("═══════════════════════════════════════", 'system', step=1)
    time.sleep(0.4)
    push(f"✦ Topic received: '{topic}'", 'info', step=1, progress=5)
    time.sleep(0.3)
    push(f"✦ Keywords: {', '.join(keywords) if keywords else 'none provided'}", 'info', step=1, progress=10)
    time.sleep(0.3)
    if image_path:
        push(f"✦ Product image uploaded: {os.path.basename(image_path)}", 'info', step=1)
    else:
        push("✦ No product image — using generic visuals", 'warn', step=1)
    time.sleep(0.4)
    push("✔ Input validation passed", 'success', step=1, progress=15)
    push_step(0, 'completed')

    # ── Step 2 ────────────────────────────────────────────────────────────────
    push_step(1, 'active')
    push("", 'system')
    push("═══════════════════════════════════════", 'system', step=2)
    push("  STEP 2 — TREND ANALYSIS", 'system', step=2)
    push("═══════════════════════════════════════", 'system', step=2)
    time.sleep(0.5)
    push("⟳ Querying YouTube Trends API…", 'info', step=2, progress=20)
    time.sleep(0.8)
    push("⟳ Scraping Google Trends for related searches…", 'info', step=2, progress=25)
    time.sleep(0.6)
    for t in random.sample(TRENDING, 3):
        time.sleep(0.3)
        push(f"  ↳ Trending: \"{t}\" — score {random.randint(72,99)}/100", 'info', step=2)
    time.sleep(0.4)
    push("⟳ Running semantic similarity analysis…", 'info', step=2, progress=35)
    time.sleep(0.7)
    push(f"✦ SEO boosters: {', '.join(random.sample(SEO_KW, 4))}", 'info', step=2, progress=40)
    time.sleep(0.5)
    push(f"✔ Trend analysis complete — competition score: {random.randint(3,7)}/10", 'success', step=2, progress=45)
    push_step(1, 'completed')

    # ── Step 3 ────────────────────────────────────────────────────────────────
    push_step(2, 'active')
    push("", 'system')
    push("═══════════════════════════════════════", 'system', step=3)
    push("  STEP 3 — SCRIPT & THUMBNAIL", 'system', step=3)
    push("═══════════════════════════════════════", 'system', step=3)
    time.sleep(0.5)
    push("⟳ Initializing GPT-4 script generation agent…", 'info', step=3, progress=50)
    time.sleep(1.0)
    push("⟳ Generating hook (0–5 sec attention grab)…", 'info', step=3)
    time.sleep(0.7)
    push("  ↳ Hook: \"You've been buying the WRONG shoes your whole life…\"", 'info', step=3)
    time.sleep(0.4)
    push("⟳ Expanding body sections: features, pros/cons, verdict…", 'info', step=3, progress=58)
    time.sleep(0.8)
    push(f"✔ Script generated — {random.randint(600,900)} words, ~{random.randint(6,9)} min read", 'success', step=3)
    time.sleep(0.4)
    push("⟳ Launching DALL-E 3 thumbnail generation…", 'info', step=3, progress=63)
    time.sleep(1.0)
    push("  ↳ Style: bold typography + product hero shot + neon accents", 'info', step=3)
    time.sleep(0.5)
    push("  ↳ A/B variant generated for CTR testing", 'info', step=3)
    time.sleep(0.5)
    push("✔ Thumbnail assets ready (1280×720 @ 300dpi)", 'success', step=3, progress=70)
    push_step(2, 'completed')

    # ── Step 4 ────────────────────────────────────────────────────────────────
    push_step(3, 'active')
    push("", 'system')
    push("═══════════════════════════════════════", 'system', step=4)
    push("  STEP 4 — VIDEO ASSEMBLY", 'system', step=4)
    push("═══════════════════════════════════════", 'system', step=4)
    time.sleep(0.5)
    push("⟳ Synthesizing voiceover via ElevenLabs TTS…", 'info', step=4, progress=73)
    time.sleep(1.2)
    push(f"  ↳ Voice: 'Nova' — {random.randint(5,9)} min {random.randint(10,59)} sec", 'info', step=4)
    time.sleep(0.4)
    push("⟳ Fetching B-roll footage from stock library…", 'info', step=4, progress=78)
    time.sleep(0.8)
    push(f"  ↳ {random.randint(8,15)} clips selected", 'info', step=4)
    time.sleep(0.4)
    push("⟳ Compositing timeline in FFmpeg renderer…", 'info', step=4, progress=83)
    time.sleep(1.0)
    push("  ↳ Applying colour grade: cinematic warm preset", 'info', step=4)
    time.sleep(0.5)
    push("  ↳ Adding lower thirds, transitions, and end screen…", 'info', step=4)
    time.sleep(0.6)
    push("⟳ Encoding final output: H.264 1080p60 AAC 320k…", 'info', step=4, progress=88)
    time.sleep(1.0)
    push(f"✔ Video assembled — {random.randint(180,540)} MB, {random.randint(5,9)}:{random.randint(10,59):02d} runtime", 'success', step=4, progress=92)
    push_step(3, 'completed')

    # ── Step 5 ────────────────────────────────────────────────────────────────
    push_step(4, 'active')
    push("", 'system')
    push("═══════════════════════════════════════", 'system', step=5)
    push("  STEP 5 — YOUTUBE PUBLISH", 'system', step=5)
    push("═══════════════════════════════════════", 'system', step=5)
    time.sleep(0.5)
    push("⟳ Authenticating with YouTube Data API v3…", 'info', step=5, progress=93)
    time.sleep(0.7)
    push("✔ OAuth token valid, channel access confirmed", 'success', step=5)
    time.sleep(0.4)
    push("⟳ Generating SEO-optimised title & description…", 'info', step=5, progress=95)
    time.sleep(0.6)
    push(f"  ↳ Title: \"{topic} — Honest Review {datetime.now().year}\"", 'info', step=5)
    time.sleep(0.3)
    push("  ↳ Tags injected: 47 high-volume keywords", 'info', step=5)
    time.sleep(0.3)
    push("⟳ Uploading video file (resumable upload)…", 'info', step=5, progress=97)
    for pct in [20, 45, 68, 89, 100]:
        time.sleep(0.4)
        push(f"  ↳ Upload progress: {pct}%", 'info', step=5)
    time.sleep(0.5)
    vid_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_', k=11))
    push(f"✔ Video published! ID: {vid_id}", 'success', step=5, progress=100)
    time.sleep(0.3)
    push(f"  ↳ https://youtube.com/watch?v={vid_id}", 'success', step=5)
    push_step(4, 'completed')

    # ── Done ──────────────────────────────────────────────────────────────────
    push("", 'system')
    push("╔══════════════════════════════════════╗", 'success')
    push("║   PIPELINE COMPLETE — ALL 5 STEPS ✔   ║", 'success')
    push("╚══════════════════════════════════════╝", 'success')
    push_done(vid_id)
    # Signal stream to close (one-shot SSE per pipeline run)
    _event_queue.put(_STOP)


# ─── Entry ────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
