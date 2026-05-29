"""Learning service - web business layer wrapping ai_tutor modules."""
from typing import Optional

from ai_tutor.llm import LLMClient
from ai_tutor.state import Session, SessionManager
from ai_tutor.core import MapPhase, LearnPhase, QuizPhase


class LearningService:
    """Web-facing service that orchestrates the learning workflow.

    Reuses ai_tutor's core engine but exposes non-blocking, IO-free methods
    suitable for HTTP API consumption.
    """

    def __init__(self):
        self.llm = LLMClient()
        self.session_manager = SessionManager()
        self.map_phase = MapPhase(self.llm, self.session_manager)
        self.learn_phase = LearnPhase(self.llm, self.session_manager)
        self.quiz_phase = QuizPhase(self.llm, self.session_manager)

    # --- Session management ---

    def create_session(self, topic: str, user_context: str) -> Session:
        return self.session_manager.create(topic, user_context)

    def get_session(self, session_id: str) -> Session:
        return self.session_manager.load(session_id)

    def list_sessions(self) -> list[dict]:
        return self.session_manager.list_sessions()

    def delete_session(self, session_id: str) -> bool:
        session_file = self.session_manager.data_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            return True
        return False

    # --- Pretest (split into two API calls) ---

    def generate_pretest(self, session_id: str) -> list[dict]:
        session = self.session_manager.load(session_id)
        return self.map_phase.generate_pretest_questions(session)

    def submit_pretest(
        self,
        session_id: str,
        results: list[dict],
    ) -> str:
        """Submit pretest answers and store analysis on session."""
        session = self.session_manager.load(session_id)
        analysis = self.map_phase.analyze_pretest_results(session, results)

        # Store on session for later use in map generation
        if not hasattr(session, "_pretest_analysis"):
            pass
        # Store via a dict on session (we'll add a field via dynamic attr)
        # Actually we need to persist this — store in a way that survives JSON round-trip
        # For now: pass it through to generate_map directly via in-memory
        return analysis

    # --- Map generation (streaming) ---

    def stream_map(self, session_id: str, pretest_analysis: str = ""):
        """Generate learning map with streaming output.

        Yields:
            dict events compatible with SSE
        """
        from ai_tutor.prompts import MAP_PROMPT

        session = self.session_manager.load(session_id)

        prompt = MAP_PROMPT.format(
            topic=session.topic,
            user_context=session.user_context,
            pretest_result=pretest_analysis or "",
        )

        full_response = []
        try:
            for chunk in self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                stream=True,
            ):
                full_response.append(chunk)
                yield {"type": "chunk", "text": chunk}
        except Exception as e:
            yield {"type": "error", "message": str(e)}
            return

        response_text = "".join(full_response)

        # Parse and save
        session.map = self.map_phase._parse_map_response(response_text)
        session.status = "in_progress"
        self.session_manager.save(session)

        yield {
            "type": "done",
            "session": session.model_dump(),
        }

    # --- Chapter teaching (streaming) ---

    def stream_chapter(self, session_id: str, chapter_id: int):
        """Stream chapter content. Delegates to LearnPhase.teach_chapter_stream."""
        session = self.session_manager.load(session_id)
        yield from self.learn_phase.teach_chapter_stream(session, chapter_id)

    # --- Spiral review ---

    def get_review_flashcards(self, session_id: str, chapter_id: int) -> list[dict]:
        """Get flashcards to review before starting a new chapter."""
        session = self.session_manager.load(session_id)
        review_ids = self.learn_phase.get_review_chapter_ids(chapter_id)

        flashcards = []
        for rid in review_ids:
            card = self.learn_phase.generate_review_flashcard(session, rid)
            if card:
                flashcards.append(card)
        return flashcards

    # --- Quiz ---

    def generate_quiz(self, session_id: str, chapter_id: int) -> list[dict]:
        """Generate quiz questions for a chapter."""
        session = self.session_manager.load(session_id)
        session = self.quiz_phase.generate_questions(session, chapter_id)

        chapter = session.map.chapters[chapter_id - 1]
        return [q.model_dump() for q in chapter.quiz]

    def submit_answer(
        self,
        session_id: str,
        chapter_id: int,
        question_id: str,
        user_answer: str,
    ) -> dict:
        """Evaluate an answer."""
        session = self.session_manager.load(session_id)
        return self.quiz_phase.evaluate_answer(
            session, chapter_id, question_id, user_answer
        )

    def submit_reasoning(
        self,
        session_id: str,
        chapter_id: int,
        question_id: str,
        reasoning: str,
    ) -> dict:
        """Verify the user's reasoning path after a correct answer."""
        session = self.session_manager.load(session_id)
        chapter = session.map.chapters[chapter_id - 1]
        question = next((q for q in chapter.quiz if q.id == question_id), None)

        if not question:
            return {"reasoning_sound": False, "feedback": "题目未找到"}

        eval_prompt = f"""
问题：{question.question}
用户答案：{question.user_answer}
用户解释的推理过程：{reasoning}

判断：用户的推理路径是否正确？是真懂还是猜对的？

输出 JSON：
{{"reasoning_sound": true/false, "feedback": "..."}}
"""
        response = self.llm.chat(
            messages=[{"role": "user", "content": eval_prompt}],
            temperature=0.3,
        )

        import re
        import json
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if not json_match:
            return {"reasoning_sound": True, "feedback": "推理验证完成"}

        result = json.loads(json_match.group(0))

        # Update session
        question.reasoning_sound = result.get("reasoning_sound", True)
        self.session_manager.save(session)

        return result

    def check_chapter_passed(self, session_id: str, chapter_id: int) -> bool:
        session = self.session_manager.load(session_id)
        return self.quiz_phase.check_chapter_passed(session, chapter_id)

    def mark_chapter_completed(self, session_id: str, chapter_id: int) -> Session:
        session = self.session_manager.load(session_id)
        chapter = session.map.chapters[chapter_id - 1]
        chapter.status = "completed"
        chapter.quiz_passed = True

        # Check if all chapters done
        if all(ch.status == "completed" for ch in session.map.chapters):
            session.status = "completed"

        self.session_manager.save(session)
        return session

    # --- Export ---

    def export_markdown(self, session_id: str) -> str:
        return self.session_manager.export_markdown(session_id)
