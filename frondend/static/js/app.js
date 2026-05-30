/**
 * YouTube Automation System — app.js
 * Uses Server-Sent Events (SSE) for real-time pipeline logs.
 */

/* ── Pipeline Steps ───────────────────────────────────────── */
const STEPS = [
  { label: 'Input<br>Trigger',      n: 1 },
  { label: 'Trend<br>Analysis',     n: 2 },
  { label: 'Script &<br>Thumbnail', n: 3 },
  { label: 'Video<br>Assembly',     n: 4 },
  { label: 'YouTube<br>Publish',    n: 5 },
];

/* ── State ────────────────────────────────────────────────── */
let keywords       = [];
let pipelineRunning= false;
let logLineCount   = 0;
let currentSSE     = null;  // active EventSource

/* ── DOM ──────────────────────────────────────────────────── */
const form            = document.getElementById('pipeline-form');
const topicInput      = document.getElementById('topic');
const topicError      = document.getElementById('topic-error');
const kwInput         = document.getElementById('keyword-input');
const kwAddBtn        = document.getElementById('keyword-add-btn');
const kwTags          = document.getElementById('keyword-tags');
const kwHidden        = document.getElementById('keywords-hidden');
const uploadZone      = document.getElementById('upload-zone');
const imageInput      = document.getElementById('image-input');
const uploadPlaceholder = document.getElementById('upload-placeholder');
const uploadPreview   = document.getElementById('upload-preview');
const previewImg      = document.getElementById('preview-img');
const removeImageBtn  = document.getElementById('remove-image-btn');
const generateBtn     = document.getElementById('generate-btn');
const genInner        = generateBtn.querySelector('.generate-btn-inner');
const genLoading      = generateBtn.querySelector('.generate-btn-loading');
const stepsContainer  = document.getElementById('pipeline-steps');
const terminalBody    = document.getElementById('terminal-body');
const terminalEmpty   = document.getElementById('terminal-empty');
const logLines        = document.getElementById('log-lines');
const clearLogsBtn    = document.getElementById('clear-logs-btn');
const statusDot       = document.getElementById('terminal-status-dot');
const statusLabel     = document.getElementById('terminal-status-label');
const lineCount       = document.getElementById('terminal-line-count');
const globalProgress  = document.getElementById('global-progress');
const connStatus      = document.getElementById('connection-status');

/* ── Init ─────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  buildStepCards();
});

/* ── Step Cards ───────────────────────────────────────────── */
function buildStepCards() {
  stepsContainer.innerHTML = '';
  STEPS.forEach((s, i) => {
    const card = document.createElement('div');
    card.className = 'step-card';
    card.dataset.index = i;
    card.innerHTML = `<div class="step-num">${s.n}</div><div class="step-label">${s.label}</div>`;
    stepsContainer.appendChild(card);
  });
}

function setStepState(index, state) {
  const cards = stepsContainer.querySelectorAll('.step-card');
  if (!cards[index]) return;
  const c = cards[index];
  c.classList.remove('active', 'completed');
  if (state === 'active')    c.classList.add('active');
  if (state === 'completed') c.classList.add('completed');
}

function resetAllSteps() {
  stepsContainer.querySelectorAll('.step-card').forEach(c => c.classList.remove('active','completed'));
}

/* ── SSE Stream ───────────────────────────────────────────── */
function openSSE() {
  if (currentSSE) { currentSSE.close(); currentSSE = null; }

  const es = new EventSource('/stream');
  currentSSE = es;

  setConnStatus('connected', 'Streaming');

  es.onmessage = (e) => {
    let envelope;
    try { envelope = JSON.parse(e.data); } catch { return; }

    if (envelope.type === 'log') {
      appendLog(envelope.data);
      if (envelope.data.progress != null) updateProgress(envelope.data.progress);

    } else if (envelope.type === 'step_update') {
      setStepState(envelope.data.index, envelope.data.status);

    } else if (envelope.type === 'pipeline_complete') {
      setRunning(false);
      setTermStatus('done', 'Pipeline complete');
      if (envelope.data.success) {
        showToast(`✔ Video published! ID: ${envelope.data.video_id}`, 'success');
      }
      es.close();
      currentSSE = null;
      setConnStatus('idle', 'Idle');
    }
  };

  es.onerror = () => {
    es.close();
    currentSSE = null;
    setConnStatus('idle', 'Idle');
    if (pipelineRunning) {
      setRunning(false);
      setTermStatus('error', 'Stream error');
    }
  };
}

function setConnStatus(type, label) {
  connStatus.className = 'status-pill ' + (type === 'connected' ? 'connected' : type === 'error' ? 'error' : '');
  connStatus.querySelector('.status-label').textContent = label;
}

/* ── Logs ─────────────────────────────────────────────────── */
function appendLog(data) {
  if (!terminalEmpty.hidden) terminalEmpty.hidden = true;

  const line = document.createElement('div');
  line.className = `log-line level-${data.level || 'info'}`;

  if (!data.message || !data.message.trim()) {
    line.innerHTML = `<span class="log-ts"> </span><span class="log-msg"> </span>`;
    logLines.appendChild(line);
    autoScroll();
    return;
  }

  const ts = data.timestamp || new Date().toLocaleTimeString('en-US',{hour12:false});
  line.innerHTML = `<span class="log-ts">${esc(ts)}</span><span class="log-msg">${esc(data.message)}</span>`;
  logLines.appendChild(line);
  logLineCount++;
  lineCount.textContent = `${logLineCount} lines`;
  autoScroll();
}

function autoScroll() { terminalBody.scrollTop = terminalBody.scrollHeight; }

function clearLogs() {
  logLines.innerHTML = '';
  logLineCount = 0;
  lineCount.textContent = '';
  terminalEmpty.hidden = false;
}

clearLogsBtn.addEventListener('click', clearLogs);

/* ── Terminal status ──────────────────────────────────────── */
function setTermStatus(state, label) {
  statusDot.className = 'terminal-status-dot ' + state;
  statusLabel.textContent = label;
}

/* ── Progress ─────────────────────────────────────────────── */
function updateProgress(pct) { globalProgress.textContent = `${pct}%`; }
function resetProgress()     { globalProgress.textContent = '0%'; }

/* ── Running State ────────────────────────────────────────── */
function setRunning(running) {
  pipelineRunning = running;
  generateBtn.disabled = running;
  genInner.hidden   =  running;
  genLoading.hidden = !running;
  if (running) setTermStatus('running', 'Pipeline running…');
}

/* ── Keywords ─────────────────────────────────────────────── */
function addKeyword(v) {
  v = v.trim();
  if (!v || keywords.includes(v) || keywords.length >= 8) return;
  keywords.push(v);
  renderTags();
  kwInput.value = '';
}

function removeKeyword(v) {
  keywords = keywords.filter(k => k !== v);
  renderTags();
}

function renderTags() {
  kwTags.innerHTML = '';
  keywords.forEach(k => {
    const tag = document.createElement('span');
    tag.className = 'keyword-tag';
    tag.innerHTML = `${esc(k)}<button type="button" class="keyword-tag-remove" aria-label="Remove ${esc(k)}">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" width="10" height="10"><path d="M18 6 6 18M6 6l12 12"/></svg>
    </button>`;
    tag.querySelector('.keyword-tag-remove').addEventListener('click', () => removeKeyword(k));
    kwTags.appendChild(tag);
  });
  kwHidden.value = keywords.join(',');
}

kwAddBtn.addEventListener('click', () => addKeyword(kwInput.value));
kwInput.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); addKeyword(kwInput.value); } });

/* ── Image Upload ─────────────────────────────────────────── */
function showPreview(file) {
  const r = new FileReader();
  r.onload = e => { previewImg.src = e.target.result; uploadPlaceholder.hidden = true; uploadPreview.hidden = false; };
  r.readAsDataURL(file);
}

function clearPreview() {
  previewImg.src = '';
  uploadPlaceholder.hidden = false;
  uploadPreview.hidden = true;
  imageInput.value = '';
}

imageInput.addEventListener('change', () => { if (imageInput.files[0]) showPreview(imageInput.files[0]); });
removeImageBtn.addEventListener('click', e => { e.stopPropagation(); clearPreview(); });

uploadZone.addEventListener('dragenter', e => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
uploadZone.addEventListener('dragover',  e => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
uploadZone.addEventListener('dragleave', e => { if (!uploadZone.contains(e.relatedTarget)) uploadZone.classList.remove('drag-over'); });
uploadZone.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  const f = e.dataTransfer.files[0];
  if (f && /\.(jpe?g|png|gif|webp)$/i.test(f.name)) {
    const dt = new DataTransfer(); dt.items.add(f); imageInput.files = dt.files; showPreview(f);
  }
});
uploadZone.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); imageInput.click(); } });

/* ── Form Submit ──────────────────────────────────────────── */
form.addEventListener('submit', async e => {
  e.preventDefault();
  const topic = topicInput.value.trim();
  if (!topic) {
    topicError.classList.add('visible');
    topicInput.classList.add('error');
    topicInput.focus();
    return;
  }
  topicError.classList.remove('visible');
  topicInput.classList.remove('error');
  if (pipelineRunning) return;

  // Open SSE before posting so we don't miss early messages
  clearLogs();
  resetAllSteps();
  resetProgress();
  setRunning(true);
  openSSE();

  const fd = new FormData();
  fd.append('topic', topic);
  fd.append('description', document.getElementById('description').value);
  fd.append('keywords', keywords.join(','));
  if (imageInput.files[0]) fd.append('image', imageInput.files[0]);

  try {
    const res  = await fetch('/generate', { method: 'POST', body: fd });
    const data = await res.json();
    if (!data.success) {
      showToast(data.error || 'Pipeline failed to start', 'error');
      setRunning(false);
      setTermStatus('error', 'Error');
      if (currentSSE) { currentSSE.close(); currentSSE = null; }
    }
  } catch (err) {
    console.error(err);
    showToast('Network error — could not reach server', 'error');
    setRunning(false);
    setTermStatus('error', 'Error');
    if (currentSSE) { currentSSE.close(); currentSSE = null; }
  }
});

topicInput.addEventListener('input', () => { topicError.classList.remove('visible'); topicInput.classList.remove('error'); });

/* ── Toast ────────────────────────────────────────────────── */
function showToast(msg, type = 'info', duration = 5000) {
  const c = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.innerHTML = `<span class="toast-dot"></span><span class="toast-text">${esc(msg)}</span>`;
  c.appendChild(t);
  setTimeout(() => { t.classList.add('removing'); setTimeout(() => t.remove(), 220); }, duration);
}

/* ── Util ─────────────────────────────────────────────────── */
function esc(s) {
  if (typeof s !== 'string') return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;');
}
