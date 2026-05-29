"""Export routes."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from web.api.sessions import get_service

router = APIRouter(prefix="/api/sessions", tags=["export"])


@router.get("/{session_id}/export", response_class=PlainTextResponse)
async def export_markdown(session_id: str):
    """Export session notes as Markdown."""
    try:
        markdown = get_service().export_markdown(session_id)
        return markdown
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
