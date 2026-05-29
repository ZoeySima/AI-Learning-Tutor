"""Export routes."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from web.service import LearningService

router = APIRouter(prefix="/api/sessions", tags=["export"])
service = LearningService()


@router.get("/{session_id}/export", response_class=PlainTextResponse)
async def export_markdown(session_id: str):
    """Export session notes as Markdown."""
    try:
        markdown = service.export_markdown(session_id)
        return markdown
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
