# Roman Scribe AI

Roman Scribe AI is a high-performance, minimalist, offline-first desktop note-taking application tailored for Business Analysts. It ensures complete privacy by keeping all transcription and API operations entirely local.

## 🚀 Features

- **Bilingual Input:** Real-time input in English and Roman Urdu with automatic conversion to native Urdu script (Nastaliq).
- **Offline Transcription:** Exact meeting transcription using a local `faster-whisper` engine.
- **Meeting Bot Integration:** Automatically joins Google Meet sessions to record audio and instantly transcribes proceedings.
- **AI Minutes of Meeting (MOM):** Automated Smart Tag extraction for project management and AI-driven generation of MOM into formatted PDF reports.
- **Split-pane Interface:** A highly responsive, split-screen UI for comparing live notes against the meeting transcripts.

## 💻 Tech Stack

- **Backend:** Python, FastAPI, SQLite, Local `faster-whisper`
- **Frontend:** React, Vite
- **Automation/Bot:** Python (Pyppeteer/undetected_chromedriver) for high-trust bot bypass
- **Scripts:** PowerShell for zero-touch setup and execution

## 🛠️ Getting Started

1. **Setup:** Double click or run `setup.ps1` to automatically install Python dependencies locally (creates a `.venv`) and Node.js modules.
2. **Launch:** Run `start.ps1` to boot up the backend API, the frontend UI, and initialize the meeting bot simultaneously.

## 🤝 Project Structure

- `/roman-scribe-api`: Core backend logic and AI audio transcription services.
- `/roman-scribe-ui`: The minimalist React-based frontend dashboard.
- `setup.ps1` & `start.ps1`: Automated bootstrapping for local Windows deployment.

---

*Built with ❤️ for Business Analysts.*
