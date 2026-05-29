"""Session management API routes."""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from web.service import LearningService

router = APIRouter(prefix="/api/sessions", tags=["sessions"])
service = LearningService()


class CreateSessionRequest(BaseModel):
    topic: str
    user_context: str


class PretestSubmission(BaseModel):
    results: list[dict]


@router.post("")
async def create_session(req: CreateSessionRequest):
    """Create a new learning session."""
    if not req.topic.strip() or not req.user_context.strip():
        raise HTTPException(status_code=400, detail="topic and user_context required")
    session = service.create_session(req.topic, req.user_context)
    return session.model_dump()


@router.get("")
async def list_sessions():
    """List all learning sessions."""
    return service.list_sessions()


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Get a session by ID."""
    try:
        session = service.get_session(session_id)
        return session.model_dump()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if service.delete_session(session_id):
        return {"deleted": True}
    raise HTTPException(status_code=404, detail="Session not found")


@router.post("/{session_id}/pretest")
async def generate_pretest(session_id: str):
    """Generate diagnostic pretest questions."""
    try:
        questions = service.generate_pretest(session_id)
        return {"questions": questions}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/{session_id}/pretest/submit")
async def submit_pretest(session_id: str, req: PretestSubmission):
    """Submit pretest answers, return analysis."""
    try:
        analysis = service.submit_pretest(session_id, req.results)
        return {"analysis": analysis}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
