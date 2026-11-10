# ViralCut AI

**ViralCut AI** is an intelligent, hardware-conscious video-processing system that automatically identifies viral moments from long-form videos and converts them into short-form vertical videos (9:16) for YouTube Shorts.

Tailored specifically for hardware-conscious environments (**HP ProDesk 400 G5 SFF**: Intel Core i3 8th Gen, 8 GB RAM, Intel Integrated Graphics, Windows 11).

---

## 📌 Complete 4-Phase System Status: ALL PHASES COMPLETED

| Phase | Description | Status |
|---|---|---|
| **Phase 1** | **Video Processing Foundation**: Video upload, metadata extraction, 16kHz mono audio extraction, Faster-Whisper CPU INT8 transcription with word timestamps, SQLite database. | ✅ Verified & Tested |
| **Phase 2** | **AI Viral Clip Detection**: Semantic sentence-aware segmentation, 6-dimension weighted viral scoring (Hook 25%, Emotion 20%, Info 15%, Story 15%, Context 15%, Engagement 10%), IoU overlap suppression, candidate ranking. | ✅ Verified & Tested |
| **Phase 3** | **Automatic Shorts Generation**: Face-tracked / centered vertical 9:16 framing ($720\times1280$), EBU R128 audio normalization, burned-in yellow styled subtitles (ASS), YouTube Shorts metadata generator. | ✅ Verified & Tested |
| **Phase 4** | **Full-Stack Application & YouTube Integration**: Interactive React dashboard, real-time analytics, HTML5 vertical video player, metadata editor, YouTube Data API v3 publishing & OAuth sync. | ✅ Verified & Tested |

---

## 🚀 Directory Structure

```
ViralCutAI/
│
├── backend/
│   ├── app.py                      # FastAPI app with REST API & Static Dashboard hosting
│   ├── config.py                   # System & hardware optimization settings
│   ├── requirements.txt            # Locked Python dependencies
│   │
│   ├── modules/
│   │   ├── video_input.py          # Video upload validation and streamed saving
│   │   ├── audio_extraction.py     # FFprobe metadata & FFmpeg audio extraction
│   │   ├── transcription.py        # Faster-Whisper CPU INT8 engine
│   │   ├── transcript_analysis.py  # Semantic sentence-boundary windowing
│   │   ├── viral_scoring.py        # 6-dimension weighted viral scoring engine
│   │   ├── clip_detection.py       # Candidate detection & IoU overlap suppression
│   │   ├── subtitle_generator.py   # Word-level styled ASS subtitle generator
│   │   ├── metadata_generator.py   # YouTube Shorts title, description, tags generator
│   │   ├── video_editor.py         # OpenCV face tracking & 9:16 FFmpeg video editor
│   │   └── youtube_upload.py       # YouTube Data API v3 & OAuth publishing engine
│   │
│   ├── database/
│   │   ├── db.py                   # SQLite tables (videos, transcripts, clips, youtube_uploads)
│   │   └── viralcut.db             # Local database
│   │
│   └── services/
│       ├── ai_service.py           # Hybrid AI service (Local rule engine + Cloud LLM)
│       └── processing_service.py   # End-to-end async background processing pipeline
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Complete React dashboard application
│   │   ├── index.css               # Modern dark SaaS design system
│   │   └── main.jsx
│   ├── dist/                       # Production compiled assets
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
│
├── tests/
│   ├── test_phase1.py              # Phase 1 verification suite
│   ├── test_phase2.py              # Phase 2 verification suite
│   ├── test_phase3.py              # Phase 3 verification suite
│   └── test_phase4.py              # Phase 4 verification suite
│
├── videos/uploads/                 # Uploaded source video storage
├── output/                         # Rendered 9:16 YouTube Shorts (.mp4)
├── models/                         # Cached Whisper weights
├── temp/                           # Temporary processing scratch space
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚡ Quick Start: Running ViralCut AI

### 1. Launch the Unified Backend & Dashboard Server
Run from PowerShell in `D:\ViralCutAI`:
```powershell
.\venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Open the Web Dashboard
Open your browser and navigate to:
👉 **`http://127.0.0.1:8000/`** (or `http://127.0.0.1:8000/dashboard`)

You can also view the interactive Swagger API documentation at:
👉 **`http://127.0.0.1:8000/docs`**

### 3. Optional: Running Frontend in Vite Development Mode
If you wish to edit the React frontend with live hot-reloading:
```powershell
cd D:\ViralCutAI\frontend
npm.cmd run dev
```
Open **`http://localhost:3000`**.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web Dashboard (browser) or System status (API client) |
| `GET` | `/api/dashboard/analytics` | Real-time counts (videos, shorts, pending, completed uploads) |
| `POST` | `/api/videos/upload` | Upload video file (`.mp4`, `.mov`, `.mkv`, `.avi`). Spawns async pipeline |
| `GET` | `/api/videos` | List all uploaded videos and statuses |
| `GET` | `/api/videos/{video_id}` | Retrieve video details & metadata (duration, resolution, fps, codec) |
| `GET` | `/api/videos/{video_id}/status` | Lightweight endpoint for UI polling |
| `GET` | `/api/videos/{video_id}/transcript` | Get full transcript text, language confidence, and timestamped segments |
| `POST` | `/api/videos/{video_id}/detect-clips`| Re-run AI viral clip detection with custom durations |
| `GET` | `/api/videos/{video_id}/clips` | Retrieve all detected viral candidate clips ranked by score |
| `GET` | `/api/clips/{clip_id}` | Retrieve details and 6-dimension scores for a specific clip |
| `PATCH`| `/api/clips/{clip_id}` | Approve/reject clip or edit working title |
| `POST` | `/api/clips/{clip_id}/render` | Render vertical 9:16 Short with face-tracking & styled subtitles |
| `GET` | `/api/clips/{clip_id}/video` | Stream / preview the rendered MP4 Short in HTML5 video player |
| `GET` | `/api/youtube/status` | Check YouTube OAuth connection status |
| `POST` | `/api/clips/{clip_id}/upload-youtube` | Publish approved Short to YouTube Shorts with privacy setting |
| `GET` | `/api/youtube/uploads` | View history of all published YouTube Shorts |
| `DELETE`| `/api/videos/{video_id}` | Delete video record, transcript, clips, and physical files |

---

## 🧪 Comprehensive Test Suite

To verify all 4 phases independently or in sequence:
```powershell
cd D:\ViralCutAI

# Run individual test suites:
.\venv\Scripts\python.exe tests\test_phase1.py
.\venv\Scripts\python.exe tests\test_phase2.py
.\venv\Scripts\python.exe tests\test_phase3.py
.\venv\Scripts\python.exe tests\test_phase4.py

# Run all 4 suites together:
.\venv\Scripts\python.exe tests\test_phase1.py; .\venv\Scripts\python.exe tests\test_phase2.py; .\venv\Scripts\python.exe tests\test_phase3.py; .\venv\Scripts\python.exe tests\test_phase4.py
```


---

## 🚀 Directory Structure

```
ViralCutAI/
│
├── backend/
│   ├── app.py                      # FastAPI application & REST endpoints
│   ├── config.py                   # System & hardware optimization settings
│   ├── requirements.txt            # Python dependencies
│   │
│   ├── modules/
│   │   ├── video_input.py          # Video upload validation and streamed saving
│   │   ├── audio_extraction.py     # FFprobe metadata & FFmpeg audio extraction
│   │   └── transcription.py        # Faster-Whisper CPU INT8 transcription engine
│   │
│   ├── database/
│   │   └── db.py                   # SQLite tables (videos, transcripts) & queries
│   │
│   └── services/
│       └── processing_service.py   # Async background video processing pipeline
│
├── tests/
│   └── test_phase1.py              # Automated test suite & benchmark
│
├── videos/
│   └── uploads/                    # Stored video files
├── output/                         # Output Shorts (Phase 3)
├── models/                         # Cached Whisper models
├── temp/                           # Temporary processing audio/scratch
├── .env.example                    # Environment variable template
└── README.md
```

---

## 🛠️ Installation & Setup (Windows)

### 1. Prerequisites
- **Python 3.12** installed on Windows.
- **FFmpeg**: Installed via Winget (`winget install Gyan.FFmpeg.Essentials`) and added to PATH.

### 2. Activate Virtual Environment & Install Packages
```powershell
cd D:\ViralCutAI
venv\Scripts\activate
pip install -r backend\requirements.txt
```

### 3. Start the Backend Server
```powershell
cd D:\ViralCutAI
venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | System health check and active phase |
| `POST` | `/api/videos/upload` | Upload video file (`.mp4`, `.mov`, `.mkv`, `.avi`). Spawns async pipeline |
| `GET` | `/api/videos` | List all uploaded videos and statuses |
| `GET` | `/api/videos/{video_id}` | Retrieve video details & metadata (duration, resolution, fps, codec) |
| `GET` | `/api/videos/{video_id}/status` | Lightweight endpoint for UI polling |
| `GET` | `/api/videos/{video_id}/transcript` | Get full transcript text, language confidence, and timestamped segments |
| `POST` | `/api/videos/{video_id}/detect-clips`| Re-run AI viral clip detection with custom durations |
| `GET` | `/api/videos/{video_id}/clips` | Retrieve all detected viral candidate clips ranked by score |
| `GET` | `/api/clips/{clip_id}` | Retrieve details and 6-dimension scores for a specific clip |
| `PATCH`| `/api/clips/{clip_id}` | Approve/reject clip or edit working title |
| `POST` | `/api/clips/{clip_id}/render` | Render vertical 9:16 Short with face-tracking & styled subtitles |
| `GET` | `/api/clips/{clip_id}/video` | Stream / preview the rendered MP4 Short in browser |
| `DELETE`| `/api/videos/{video_id}` | Delete video record, transcript, clips, and physical files |

---

## 🧪 Automated Testing & Benchmark Results

Run the verification suites:
```powershell
# Phase 1 Test (Video upload, audio extraction, Whisper INT8 transcription)
venv\Scripts\python.exe tests\test_phase1.py

# Phase 2 Test (Viral scoring, transcript segmentation, clip ranking & API flow)
venv\Scripts\python.exe tests\test_phase2.py

# Phase 3 Test (Vertical 9:16 render, face-tracking, subtitles, video streaming)
venv\Scripts\python.exe tests\test_phase3.py
```

### Benchmark Summary (Intel Core i3 8th Gen, 8GB RAM, CPU INT8):
- **Video Metadata Inspection**: < 50ms
- **Audio Extraction**: < 100ms
- **Faster-Whisper Tiny (CPU INT8)**: ~2.29 seconds for 11.05s audio (~4.8x real-time speed)
- **Memory Footprint**: ~400 MB RAM during inference
- **Result**: 100% Passed
