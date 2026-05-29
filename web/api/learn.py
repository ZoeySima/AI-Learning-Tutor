"""Learning routes (map, chapter teaching, quiz) with SSE streaming."""
import json
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from web.api.sessions import get_service

router = APIRouter(prefix="/api/sessions", tags=["learn"])


class MapRequest(BaseModel):
    pretest_analysis: Optional[str] = ""


class AnswerRequest(BaseModel):
    question_id: str
    answer: str


class ReasoningRequest(BaseModel):
    question_id: str
    reasoning: str


def sse_format(event: dict) -> str:
    """Format a dict as an SSE frame."""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/{session_id}/map")
async def stream_map(session_id: str, req: MapRequest):
    """Generate learning map with SSE streaming."""

    def event_stream():
        try:
            for event in get_service().stream_map(session_id, req.pretest_analysis or ""):
                yield sse_format(event)
        except FileNotFoundError:
            yield sse_format({"type": "error", "message": "Session not found"})
        except Exception as e:
            yield sse_format({"type": "error", "message": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/{session_id}/chapters/{chapter_id}/teach")
async def stream_chapter(session_id: str, chapter_id: int):
    """Stream chapter teaching content via SSE."""

    def event_stream():
        try:
            for event in get_service().stream_chapter(session_id, chapter_id):
                yield sse_format(event)
        except FileNotFoundError:
            yield sse_format({"type": "error", "message": "Session not found"})
        except Exception as e:
            yield sse_format({"type": "error", "message": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/{session_id}/chapters/{chapter_id}/review")
async def get_review(session_id: str, chapter_id: int):
    """Get spiral review flashcards before starting a new chapter."""
    try:
        flashcards = get_service().get_review_flashcards(session_id, chapter_id)
        return {"flashcards": flashcards}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/{session_id}/chapters/{chapter_id}/quiz")
async def generate_quiz(session_id: str, chapter_id: int):
    """Generate quiz questions for a chapter."""
    try:
        questions = get_service().generate_quiz(session_id, chapter_id)
        return {"questions": questions}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/chapters/{chapter_id}/answer")
async def submit_answer(session_id: str, chapter_id: int, req: AnswerRequest):
    """Submit an answer to a quiz question."""
    try:
        result = get_service().submit_answer(
            session_id, chapter_id, req.question_id, req.answer
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/chapters/{chapter_id}/reasoning")
async def submit_reasoning(session_id: str, chapter_id: int, req: ReasoningRequest):
    """Submit reasoning path for a correctly-answered question."""
    try:
        result = get_service().submit_reasoning(
            session_id, chapter_id, req.question_id, req.reasoning
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/{session_id}/chapters/{chapter_id}/complete")
async def complete_chapter(session_id: str, chapter_id: int):
    """Mark chapter as completed."""
    try:
        if not get_service().check_chapter_passed(session_id, chapter_id):
            raise HTTPException(status_code=400, detail="Chapter not passed yet")
        session = get_service().mark_chapter_completed(session_id, chapter_id)
        return session.model_dump()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
