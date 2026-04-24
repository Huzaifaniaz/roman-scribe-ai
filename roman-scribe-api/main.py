import os
from dotenv import load_dotenv

# Load E: drive storage paths from .env before anything else
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Fix for some system path variables being empty affecting webview
if not os.environ.get("Path"):
    os.environ["Path"] = ""

# Ensure models and recordings use E: drive
E_DRIVE_BASE = "E:/notetaking"
os.makedirs(os.path.join(E_DRIVE_BASE, "recordings"), exist_ok=True)
os.makedirs(os.path.join(E_DRIVE_BASE, ".cache"), exist_ok=True)

from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import webview
import threading
import asyncio
from database import init_db, SessionLocal, Note, SmartTag
from meeting_bot import MeetingBot
from fpdf import FPDF
import tempfile

init_db()

app = FastAPI(title="Roman-Scribe AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global bot instance
current_bot = None
bot_status = {
    "is_running": False, 
    "transcribing": False, 
    "last_transcript": "",
    "logs": ["Backend initialized."]
}

def add_bot_log(msg):
    bot_status["logs"].append(msg)
    if len(bot_status["logs"]) > 10:
        bot_status["logs"].pop(0)

class TranslationRequest(BaseModel):
    text: str

class ExportRequest(BaseModel):
    english_text: str
    urdu_text: str

class MeetingRequest(BaseModel):
    url: str
    name: str = "Roman-Scribe Assistant"

# Load models with E: drive cache paths
try:
    from faster_whisper import WhisperModel
    # Model will download to E:/notetaking/.cache/whisper as per .env
    model_path = os.getenv("WHISPER_MODEL_DIR", "E:/notetaking/.cache/whisper")
    whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8", download_root=model_path)
except Exception as e:
    print(f"Whisper Error: {e}")
    whisper_model = None

# Summarizer setup (Disabled for now to fix 'unknown task' errors during core bot testing)
summarizer = None
# try:
#     from transformers import pipeline
#     # Cache handled by HF_HOME in .env
#     summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", device="cpu")
# except Exception as e:
#     print(f"Summarizer Error: {e}")
#     summarizer = None

@app.post("/api/translate")
async def translate_text(request: TranslationRequest):
    text = request.text
    # Mock offline translation
    mocked_urdu = text.replace("kaha", "کہا").replace("hai", "ہے").replace("toh", "تو").replace("humein", "ہمیں")
    return {"translated_text": mocked_urdu}

@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    if not whisper_model:
        return {"text": "[Whisper model not loaded]"}
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
        
    segments, info = whisper_model.transcribe(tmp_path, beam_size=5)
    result_text = " ".join([segment.text for segment in segments])
    os.remove(tmp_path)
    return {"text": result_text.strip()}

@app.post("/api/meeting/join")
async def join_meeting(request: MeetingRequest):
    global current_bot
    if current_bot and current_bot.is_running:
        return {"status": "error", "message": "Bot already in a meeting"}
    
    current_bot = MeetingBot(request.url, request.name, log_callback=add_bot_log)
    
    # Run bot in a separate event loop/thread to not block FastAPI
    def start_bot():
        add_bot_log(f"Bot session starting for {request.name}")
        asyncio.run(current_bot.start())
    
    thread = threading.Thread(target=start_bot, daemon=True)
    thread.start()
    bot_status["is_running"] = True
    return {"status": "success", "message": "Bot joining meeting..."}

@app.post("/api/meeting/stop")
async def stop_meeting():
    global current_bot
    if not current_bot:
        return {"status": "error", "message": "No active bot"}
        
    if bot_status["transcribing"]:
        return {"status": "info", "message": "Transcription already in progress"}
    
    bot_status["transcribing"] = True
    add_bot_log("Stop requested. Finalizing recording...")
    
    # Use existing event loop for async stop to avoid runtime errors
    try:
        # If we're already in an async context, we just await it 
        # (FastAPI endpoints are naturally async if defined as async def)
        video_path = await current_bot.stop()
    except Exception as e:
        add_bot_log(f"Error stopping bot: {e}")
        bot_status["transcribing"] = False
        return {"status": "error", "message": str(e)}
    
    transcript = ""
    if video_path and whisper_model:
        add_bot_log("Starting AI transcription (FasterWhisper)...")
        # Use task="translate" to automatically convert Urdu/Mixed audio to English notes
        segments, info = whisper_model.transcribe(video_path, beam_size=5, task="translate")
        transcript = " ".join([segment.text for segment in segments])
        bot_status["last_transcript"] = transcript
        add_bot_log("Transcription complete.")
    
    bot_status["is_running"] = False
    bot_status["transcribing"] = False
    current_bot = None
    
    return {"status": "success", "transcript": transcript}

@app.get("/api/meeting/status")
async def get_meeting_status():
    return bot_status

class SaveRequest(BaseModel):
    title: str
    content_raw: str
    content_urdu: str
    tags: list[str]

@app.post("/api/save")
async def save_session(request: SaveRequest):
    db = SessionLocal()
    try:
        new_note = Note(
            title=request.title,
            content_raw=request.content_raw,
            content_urdu=request.content_urdu
        )
        db.add(new_note)
        db.commit()
        db.refresh(new_note)
        
        for t in request.tags:
            tag = SmartTag(note_id=new_note.id, tag_text=t)
            db.add(tag)
        db.commit()
        return {"status": "success", "id": new_note.id}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@app.get("/api/archive")
async def get_archive():
    db = SessionLocal()
    try:
        notes = db.query(Note).order_by(Note.created_at.desc()).all()
        result = []
        for n in notes:
            tags = db.query(SmartTag).filter(SmartTag.note_id == n.id).all()
            result.append({
                "id": n.id,
                "title": n.title,
                "content_raw": n.content_raw,
                "content_urdu": n.content_urdu,
                "created_at": n.created_at.isoformat(),
                "tags": [t.tag_text for t in tags]
            })
        return result
    finally:
        db.close()

@app.post("/api/export")
async def export_pdf(request: ExportRequest):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="Roman-Scribe AI - Meeting Notes", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="English / Roman Urdu Notes:", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 10, txt=request.english_text)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Urdu Summary (Nastaliq required for full rendering):", ln=True)
    pdf.set_font("Arial", size=10)
    # Basic PDF rendering (Nastaliq support would require .ttf embedding)
    pdf.multi_cell(0, 10, txt=request.urdu_text)
    
    pdf_path = os.path.join(tempfile.gettempdir(), "RomanScribe_Notes.pdf")
    pdf.output(pdf_path)
    return FileResponse(pdf_path, media_type='application/pdf', filename="RomanScribe_Notes.pdf")

@app.post("/api/summarize")
async def summarize_notes(request: TranslationRequest):
    text = request.text
    if not text or len(text) < 10:
        return {"mom": "Not enough text.", "key_points": ""}
    
    if summarizer:
        summary = summarizer(text[:1024], max_length=130, min_length=10, do_sample=False)[0]['summary_text']
        return {"mom": summary, "key_points": "- " + summary.replace(". ", ".\n- ")}
    else:
        lines = [line.strip() for line in text.split('\n') if "task:" in line.lower() or "action:" in line.lower()]
        pts = "\n".join(lines)
        return {"mom": "Generated Minutes (Fallback Mode).", "key_points": pts if pts else "- No tasks found."}

def start_api():
    uvicorn.run(app, host="127.0.0.1", port=8000)

def is_port_open(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('127.0.0.1', port)) == 0: return True
    try:
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
            if s.connect_ex(('::1', port)) == 0: return True
    except: pass
    return False

def wait_for_ui(port, timeout=30):
    import time
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_open(port):
            return True
        time.sleep(1)
    return False

if __name__ == "__main__":
    import subprocess
    ui_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'roman-scribe-ui'))
    
    # Start UI if not already running (port 5173 check)
    if not is_port_open(5173):
        print(f"Starting Frontend (Vite) in {ui_dir}...")
        # Use shell=True for Windows to find npm
        subprocess.Popen(["npm", "run", "dev"], cwd=ui_dir, shell=True)
    
    # Start Backend API
    print("Starting Backend API (Uvicorn) on http://127.0.0.1:8000...")
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()

    # Wait for UI to be ready before opening window
    print("Waiting for UI to be ready at http://localhost:5173...")
    if wait_for_ui(5173, timeout=45):
        ui_url = "http://localhost:5173"
        print(f"UI Ready. Launching Window...")
        window = webview.create_window('Roman-Scribe AI', ui_url, width=1280, height=800, background_color='#0d0f1a')
        webview.start()
    else:
        print("Error: UI failed to start within timeout. Please run 'npm run dev' manually in roman-scribe-ui.")
