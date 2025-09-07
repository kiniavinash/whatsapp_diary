from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
import shutil
from pathlib import Path

from .services.db import Base, engine, get_session, Message
from .services.importer import import_export_file


ROOT_DIR = Path(__file__).resolve().parent.parent
EXPORTS_DIR = ROOT_DIR / "exports"
STATIC_DIR = ROOT_DIR / "static"


def ensure_dirs() -> None:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT_DIR / "data").mkdir(parents=True, exist_ok=True)


ensure_dirs()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="WhatsApp Diary")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    html_path = STATIC_DIR / "index.html"
    if not html_path.exists():
        return HTMLResponse("<h1>WhatsApp Diary</h1><p>UI not found.</p>")
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.post("/import")
async def import_chat(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt exports are supported")
    temp_path = EXPORTS_DIR / file.filename
    with temp_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    with get_session() as session:
        summary = import_export_file(temp_path, session)

    return JSONResponse({"status": "ok", "imported": summary["imported"], "skipped": summary["skipped"], "filename": file.filename})


@app.get("/search")
def search(q: str, limit: int = 20):
    # Simple LIKE search as an initial capability; RAG will be added later
    q_like = f"%{q}%"
    with get_session() as session:
        rows = (
            session.query(Message)
            .filter(Message.text.ilike(q_like))
            .order_by(Message.timestamp.desc())
            .limit(limit)
            .all()
        )
        results = [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "sender": r.sender,
                "text": r.text,
            }
            for r in rows
        ]
    return {"results": results}


@app.post("/ask")
def ask(question: str = Form(...), limit: int = 10):
    # Placeholder: naive search fallback; will be replaced by RAG
    return search(question, limit=limit)


