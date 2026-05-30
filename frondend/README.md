# YouTube Automation System

A dark-themed SaaS dashboard simulating a 5-step AI video production pipeline with real-time WebSocket log streaming.

## Overview

This Flask application provides a production-ready dashboard UI for a YouTube content automation workflow:

```
Input Trigger → Trend Analysis → Script & Thumbnail → Video Assembly → YouTube Publish
```

Each stage streams live log output to the terminal panel via WebSocket (Flask-SocketIO), with animated pipeline step cards that reflect the current state.

## Tech Stack

- **Backend**: Flask 3 + Flask-SocketIO
- **Frontend**: Vanilla JS + CSS custom properties (no framework)
- **Fonts**: Syne (UI) + JetBrains Mono (terminal)
- **Real-time**: Socket.IO v4

## Setup & Run

```bash
# 1. Clone / extract project
cd youtube_automation

# 2. (Optional) create a virtual environment
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the development server
python app.py
```

Open your browser at **http://localhost:5000**

## Project Structure

```
youtube_automation/
├── app.py                  # Flask app + pipeline simulation + SocketIO
├── requirements.txt
├── README.md
├── uploads/                # Server-side upload storage
├── templates/
│   └── index.html          # Single-page dashboard
└── static/
    ├── css/
    │   └── style.css       # Full dark-theme stylesheet
    ├── js/
    │   └── app.js          # WebSocket + form + UI logic
    └── uploads/            # Publicly served uploaded images
```

## Features

- **Drag & drop** image upload with live preview
- **Keyword tag** input with add/remove
- **5-step animated pipeline** — pending / active (glowing pulse) / completed (checkmark)
- **Terminal log panel** — MacOS traffic lights, auto-scroll, coloured log levels
- **Toast notifications** on completion
- **WebSocket streaming** — logs appear in real time as the pipeline runs
- **Fully responsive** down to mobile

## Screenshots

_(Add screenshots here)_

## License

MIT
