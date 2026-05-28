"""State management for learning sessions."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class QuizQuestion(BaseModel):
    """Single quiz question."""
    id: str
    question: str
    type: str  # concept | application | comparison
    user_answer: Optional[str] = None
    correct: Optional[bool] = None
    feedback: Optional[str] = None


class ChapterContent(BaseModel):
    """Content for a single chapter."""
    user_perspective: str = ""
    business_perspective: str = ""
    implementer_perspective: str = ""
    examples: list[str] = Field(default_factory=list)


class Chapter(BaseModel):
    """Single chapter in the learning map."""
    id: int
    title: str
    description: str = ""
    content: Optional[ChapterContent] = None
    quiz: list[QuizQuestion] = Field(default_factory=list)
    quiz_passed: bool = False
    status: str = "pending"  # pending | in_progress | completed


class LearningMap(BaseModel):
    """Overall learning map."""
    overview: str = ""
    chapters: list[Chapter] = Field(default_factory=list)
    relationships: str = ""


class Session(BaseModel):
    """Learning session state."""
    session_id: str
    topic: str
    user_context: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: str = "draft"  # draft | in_progress | completed
    map: Optional[LearningMap] = None
    current_chapter_id: int = 0


class SessionManager:
    """Manage learning sessions."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path.home() / ".ai-tutor"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def create(self, topic: str, user_context: str) -> Session:
        """Create new learning session."""
        # Generate session ID from topic and timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        topic_slug = "".join(c if c.isalnum() else "-" for c in topic.lower())[:30]
        session_id = f"{timestamp}-{topic_slug}"

        session = Session(
            session_id=session_id,
            topic=topic,
            user_context=user_context,
            status="draft",
        )
        self.save(session)
        return session

    def load(self, session_id: str) -> Session:
        """Load existing session."""
        session_file = self.data_dir / f"{session_id}.json"
        if not session_file.exists():
            raise FileNotFoundError(f"Session {session_id} not found")

        with open(session_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Session(**data)

    def save(self, session: Session):
        """Save session to disk."""
        session.updated_at = datetime.now().isoformat()
        session_file = self.data_dir / f"{session.session_id}.json"

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session.model_dump(), f, ensure_ascii=False, indent=2)

    def list_sessions(self) -> list[dict]:
        """List all sessions."""
        sessions = []
        for session_file in self.data_dir.glob("*.json"):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append({
                    "session_id": data["session_id"],
                    "topic": data["topic"],
                    "status": data["status"],
                    "created_at": data["created_at"],
                })
            except Exception:
                continue
        return sorted(sessions, key=lambda x: x["created_at"], reverse=True)

    def export_markdown(self, session_id: str) -> str:
        """Export session as Markdown."""
        session = self.load(session_id)
        lines = [
            f"# {session.topic}",
            "",
            f"**学习背景**：{session.user_context}",
            f"**创建时间**：{session.created_at}",
            f"**状态**：{session.status}",
            "",
        ]

        if session.map:
            lines.extend([
                "## 全局概览",
                "",
                session.map.overview,
                "",
                "## 章节大纲",
                "",
            ])
            for ch in session.map.chapters:
                lines.append(f"{ch.id}. {ch.title} - {ch.status}")
            lines.append("")

            if session.map.relationships:
                lines.extend([
                    "## 章节关系",
                    "",
                    session.map.relationships,
                    "",
                ])

            # Export completed chapters
            for ch in session.map.chapters:
                if ch.status == "completed" and ch.content:
                    lines.extend([
                        f"## 第 {ch.id} 章：{ch.title}",
                        "",
                        "### 用户视角",
                        ch.content.user_perspective,
                        "",
                        "### 业务方视角",
                        ch.content.business_perspective,
                        "",
                        "### 实现者视角",
                        ch.content.implementer_perspective,
                        "",
                        "### 真实例子",
                    ])
                    for i, ex in enumerate(ch.content.examples, 1):
                        lines.append(f"{i}. {ex}")
                    lines.append("")

                    if ch.quiz:
                        lines.extend(["### 测验", ""])
                        for q in ch.quiz:
                            lines.extend([
                                f"**问题**：{q.question}",
                                f"**我的答案**：{q.user_answer or '(未作答)'}",
                                f"**结果**：{'✅ 正确' if q.correct else '❌ 错误'}",
                                f"**反馈**：{q.feedback or ''}",
                                "",
                            ])

        return "\n".join(lines)
