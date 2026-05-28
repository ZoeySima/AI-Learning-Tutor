"""Core learning engine - Map/Learn/Quiz/Loop."""
import json
import re
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown

from .llm import LLMClient
from .prompts import MAP_PROMPT, LEARN_PROMPT, QUIZ_PROMPT, EVAL_PROMPT
from .state import (
    Session,
    LearningMap,
    Chapter,
    ChapterContent,
    QuizQuestion,
    SessionManager,
)

console = Console()


class MapPhase:
    """Generate learning map (chapter outline)."""

    def __init__(self, llm: LLMClient, session_manager: SessionManager):
        self.llm = llm
        self.session_manager = session_manager

    def generate_outline(self, session: Session) -> Session:
        """Generate chapter outline for the topic."""
        console.print("\n[cyan]正在生成学习地图...[/cyan]\n")

        prompt = MAP_PROMPT.format(
            topic=session.topic,
            user_context=session.user_context,
        )

        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        # Parse response
        session.map = self._parse_map_response(response)
        session.status = "in_progress"
        self.session_manager.save(session)

        # Display map
        self._display_map(session.map)
        return session

    def _parse_map_response(self, response: str) -> LearningMap:
        """Parse LLM response into LearningMap."""
        # Extract sections
        overview_match = re.search(r"## 全局概览\s*\n(.*?)(?=\n##|$)", response, re.DOTALL)
        chapters_match = re.search(r"## 章节大纲\s*\n(.*?)(?=\n##|$)", response, re.DOTALL)
        relationships_match = re.search(r"## 章节关系\s*\n(.*?)(?=\n##|$)", response, re.DOTALL)

        overview = overview_match.group(1).strip() if overview_match else ""
        relationships = relationships_match.group(1).strip() if relationships_match else ""

        # Parse chapters
        chapters = []
        if chapters_match:
            chapter_text = chapters_match.group(1).strip()
            for line in chapter_text.split("\n"):
                # Match "1. Title: Description" or "1. Title - Description"
                match = re.match(r"(\d+)\.\s*([^:：\-]+)[:：\-]\s*(.*)", line.strip())
                if match:
                    ch_id, title, desc = match.groups()
                    chapters.append(
                        Chapter(
                            id=int(ch_id),
                            title=title.strip(),
                            description=desc.strip(),
                            status="pending",
                        )
                    )

        return LearningMap(
            overview=overview,
            chapters=chapters,
            relationships=relationships,
        )

    def _display_map(self, learning_map: LearningMap):
        """Display learning map to user."""
        console.print("━" * 60)
        console.print("[bold cyan]📚 学习地图[/bold cyan]")
        console.print("━" * 60)
        console.print()

        console.print("[bold]全局概览：[/bold]")
        console.print(Markdown(learning_map.overview))
        console.print()

        console.print("[bold]章节大纲：[/bold]")
        for ch in learning_map.chapters:
            console.print(f"  {ch.id}. {ch.title}（{ch.description}）")
        console.print()

        if learning_map.relationships:
            console.print("[bold]章节关系：[/bold]")
            console.print(learning_map.relationships)
            console.print()

        console.print("━" * 60)


class LearnPhase:
    """Teach chapter content with three perspectives."""

    def __init__(self, llm: LLMClient, session_manager: SessionManager):
        self.llm = llm
        self.session_manager = session_manager

    def teach_chapter(self, session: Session, chapter_id: int) -> Session:
        """Teach a specific chapter."""
        if not session.map or chapter_id > len(session.map.chapters):
            raise ValueError(f"Invalid chapter ID: {chapter_id}")

        chapter = session.map.chapters[chapter_id - 1]
        chapter.status = "in_progress"
        session.current_chapter_id = chapter_id
        self.session_manager.save(session)

        console.print(f"\n[cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]")
        console.print(f"[bold cyan]📖 第 {chapter.id} 章：{chapter.title}[/bold cyan]")
        console.print(f"[cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]\n")

        # Get previous chapters for context
        previous_chapters = "\n".join(
            f"{ch.id}. {ch.title}" for ch in session.map.chapters[:chapter_id - 1]
        )

        prompt = LEARN_PROMPT.format(
            chapter_title=chapter.title,
            user_context=session.user_context,
            previous_chapters=previous_chapters or "无",
        )

        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=6000,
        )

        # Parse and save content
        chapter.content = self._parse_chapter_content(response)
        self.session_manager.save(session)

        # Display content
        self._display_chapter_content(chapter.content)

        return session

    def _parse_chapter_content(self, response: str) -> ChapterContent:
        """Parse chapter content from LLM response."""
        user_match = re.search(r"【用户视角】\s*\n(.*?)(?=\n【|$)", response, re.DOTALL)
        business_match = re.search(r"【业务方视角】\s*\n(.*?)(?=\n【|$)", response, re.DOTALL)
        implementer_match = re.search(r"【实现者视角】\s*\n(.*?)(?=\n【|$)", response, re.DOTALL)
        examples_match = re.search(r"【真实例子】\s*\n(.*?)$", response, re.DOTALL)

        examples = []
        if examples_match:
            examples_text = examples_match.group(1).strip()
            # Extract examples (lines starting with "例子" or numbered)
            for line in examples_text.split("\n"):
                if line.strip() and (line.startswith("例子") or re.match(r"\d+\.", line)):
                    examples.append(line.strip())

        return ChapterContent(
            user_perspective=user_match.group(1).strip() if user_match else "",
            business_perspective=business_match.group(1).strip() if business_match else "",
            implementer_perspective=implementer_match.group(1).strip() if implementer_match else "",
            examples=examples,
        )

    def _display_chapter_content(self, content: ChapterContent):
        """Display chapter content to user."""
        console.print("[bold yellow]【用户视角】[/bold yellow]")
        console.print(Markdown(content.user_perspective))
        console.print()

        console.print("[bold yellow]【业务方视角】[/bold yellow]")
        console.print(Markdown(content.business_perspective))
        console.print()

        console.print("[bold yellow]【实现者视角】[/bold yellow]")
        console.print(Markdown(content.implementer_perspective))
        console.print()

        if content.examples:
            console.print("[bold yellow]【真实例子】[/bold yellow]")
            for ex in content.examples:
                console.print(f"  {ex}")
            console.print()

        console.print("━" * 60)


class QuizPhase:
    """Generate and evaluate quiz questions."""

    def __init__(self, llm: LLMClient, session_manager: SessionManager):
        self.llm = llm
        self.session_manager = session_manager

    def generate_questions(self, session: Session, chapter_id: int) -> Session:
        """Generate quiz questions for a chapter."""
        chapter = session.map.chapters[chapter_id - 1]

        if not chapter.content:
            raise ValueError(f"Chapter {chapter_id} has no content yet")

        console.print(f"\n[cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]")
        console.print(f"[bold cyan]📝 第 {chapter.id} 章测验（3 题）[/bold cyan]")
        console.print(f"[cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]\n")

        # Summarize chapter content
        content_summary = f"""
用户视角：{chapter.content.user_perspective[:200]}...
业务方视角：{chapter.content.business_perspective[:200]}...
实现者视角：{chapter.content.implementer_perspective[:200]}...
"""

        prompt = QUIZ_PROMPT.format(
            chapter_title=chapter.title,
            chapter_content=content_summary,
        )

        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
        )

        # Parse questions
        questions = self._parse_questions(response)
        chapter.quiz = questions
        self.session_manager.save(session)

        return session

    def _parse_questions(self, response: str) -> list[QuizQuestion]:
        """Parse quiz questions from JSON response."""
        # Extract JSON array
        json_match = re.search(r"\[.*\]", response, re.DOTALL)
        if not json_match:
            raise ValueError("Failed to parse quiz questions")

        questions_data = json.loads(json_match.group(0))
        return [QuizQuestion(**q) for q in questions_data]

    def evaluate_answer(
        self,
        session: Session,
        chapter_id: int,
        question_id: str,
        user_answer: str,
    ) -> tuple[bool, str, Optional[str]]:
        """Evaluate user's answer to a question."""
        chapter = session.map.chapters[chapter_id - 1]
        question = next((q for q in chapter.quiz if q.id == question_id), None)

        if not question:
            raise ValueError(f"Question {question_id} not found")

        # Get chapter content for evaluation
        content_summary = f"""
用户视角：{chapter.content.user_perspective}
业务方视角：{chapter.content.business_perspective}
实现者视角：{chapter.content.implementer_perspective}
"""

        prompt = EVAL_PROMPT.format(
            question=question.question,
            user_answer=user_answer,
            chapter_content=content_summary,
        )

        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        # Parse evaluation
        eval_data = self._parse_evaluation(response)

        # Update question
        question.user_answer = user_answer
        question.correct = eval_data["correct"]
        question.feedback = eval_data["feedback"]

        self.session_manager.save(session)

        return (
            eval_data["correct"],
            eval_data["feedback"],
            eval_data.get("hint"),
        )

    def _parse_evaluation(self, response: str) -> dict:
        """Parse evaluation result from JSON response."""
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if not json_match:
            raise ValueError("Failed to parse evaluation")

        return json.loads(json_match.group(0))

    def check_chapter_passed(self, session: Session, chapter_id: int) -> bool:
        """Check if all questions in chapter are answered correctly."""
        chapter = session.map.chapters[chapter_id - 1]
        return all(q.correct for q in chapter.quiz if q.correct is not None)
