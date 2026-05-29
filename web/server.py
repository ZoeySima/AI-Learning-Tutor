"""FastAPI server entry point."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from web.api import sessions, learn, export

app = FastAPI(
    title="AI Learning Tutor",
    description="Web UI for AI Learning Tutor",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(learn.router)
app.include_router(export.router)


STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/learn")
async def learn_page():
    return FileResponse(STATIC_DIR / "learn.html")


@app.get("/sessions")
async def sessions_page():
    return FileResponse(STATIC_DIR / "sessions.html")


@app.get("/notes")
async def notes_page():
    return FileResponse(STATIC_DIR / "notes.html")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.3.0"}


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def main():
    """Entry point for `python -m web.server` or start scripts."""
    import os
    import sys
    import io
    import socket
    import uvicorn

    # Fix Windows GBK encoding for stdout
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    # Find available port (8766+)
    port = int(os.getenv("AI_TUTOR_PORT", "8766"))
    for candidate in range(port, port + 15):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("127.0.0.1", candidate))
            sock.close()
            port = candidate
            break
        except OSError:
            continue
    else:
        print(f"[ERROR] No available port in range {port}-{port+15}")
        return

    print(f"[OK] Starting AI Learning Tutor at http://localhost:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
