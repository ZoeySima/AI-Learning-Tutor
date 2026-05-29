"""Core learning engine - Map/Learn/Quiz/Loop."""
import json
import re
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown

from .llm import LLMClient
from .prompts import (
    MAP_PROMPT,
    LEARN_PROMPT,
    QUIZ_PROMPT,
    EVAL_PROMPT,
    DIAGNOSTIC_PRETEST_PROMPT,
)
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

    def generate_outline(self, session: Session, skip_pretest: bool = False) -> Session:
        """Generate chapter outline for the topic.

        Args:
            session: Learning session
            skip_pretest: If True, skip diagnostic pretest

        Returns:
            Updated session with learning map
        """
        pretest_result = ""

        # Run diagnostic pretest (unless skipped)
        if not skip_pretest:
            console.print("\n[cyan]📋 诊断性前测（评估先备知识）[/cyan]\n")
            pretest_result = self._run_diagnostic_pretest(session)

        console.print("\n[cyan]正在生成学习地图...[/cyan]\n")

        prompt = MAP_PROMPT.format(
            topic=session.topic,
            user_context=session.user_context,
            pretest_result=pretest_result,
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

    def _run_diagnostic_pretest(self, session: Session) -> str:
        """Run diagnostic pretest to assess prior knowledge.

        Returns:
            Summary of pretest results for MAP_PROMPT
        """
        # Generate pretest questions
        prompt = DIAGNOSTIC_PRETEST_PROMPT.format(
            topic=session.topic,
            user_context=session.user_context,
        )

        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        # Parse questions
        json_match = re.search(r"\[.*\]", response, re.DOTALL)
        if not json_match:
            console.print("[yellow]⚠️  前测生成失败，跳过此步骤[/yellow]")
            return ""

        questions = json.loads(json_match.group(0))

        # Ask user
        from rich.prompt import Prompt

        results = []
        for i, q in enumerate(questions, 1):
            console.print(f"\n[bold]前测 {i}/{len(questions)}：[/bold]")
            console.print(q["question"])
            console.print(f"[dim]（目的：{q['purpose']}）[/dim]\n")

            answer = Prompt.ask("[yellow]你的回答[/yellow]", default="不知道")
            results.append({
                "question": q["question"],
                "answer": answer,
                "purpose": q["purpose"],
            })

        # Analyze results
        analysis_prompt = f"""
用户想学「{session.topic}」，我们做了诊断性前测，结果如下：

{chr(10).join(f"Q: {r['question']}\nA: {r['answer']}\n目的: {r['purpose']}" for r in results)}

请分析：
1. 用户的先备知识水平如何？（强/中/弱）
2. 哪些基础概念需要补充？
3. 学习地图应该如何调整深度？

输出简短总结（2-3句话），供生成学习地图时参考。
"""

        analysis = self.llm.chat(
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.5,
        )

        console.print(f"\n[dim]📊 前测分析：{analysis}[/dim]")

        return f"前测结果：{analysis}"

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
        """Display learning map to user with visual progress."""
        from rich.table import Table
        from rich.panel import Panel

        console.print("━" * 60)
        console.print("[bold cyan]📚 学习地图[/bold cyan]")
        console.print("━" * 60)
        console.print()

        console.print("[bold]全局概览：[/bold]")
        console.print(Markdown(learning_map.overview))
        console.print()

        # Visual chapter tree
        console.print("[bold]章节大纲（树状图）：[/bold]\n")
        for ch in learning_map.chapters:
            prefix = "├─" if ch.id < len(learning_map.chapters) else "└─"
            console.print(f"  {prefix} {ch.id}. [cyan]{ch.title}[/cyan]")
            console.print(f"     └─ [dim]{ch.description}[/dim]")
        console.print()

        # Progress bar (all pending at start)
        total = len(learning_map.chapters)
        completed = sum(1 for ch in learning_map.chapters if ch.status == "completed")
        progress_bar = "▓" * completed + "░" * (total - completed)
        console.print(f"[bold]学习进度：[/bold] {progress_bar} {completed}/{total}")
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

        # Spaced repetition: review previous chapters
        if chapter_id > 1:
            self._spiral_review(session, chapter_id)

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

        # Fact-check for critical domains
        verification = self.llm.verify_facts(response, session.topic)

        if verification["is_critical"]:
            if not verification["verified"]:
                console.print("\n[yellow]⚠️  事实核查发现以下问题：[/yellow]")
                for issue in verification["issues"]:
                    severity_color = {
                        "high": "red",
                        "medium": "yellow",
                        "low": "dim"
                    }.get(issue["severity"], "yellow")
                    console.print(f"[{severity_color}]  • {issue['description']}[/{severity_color}]")

                console.print("\n[cyan]正在修正内容...[/cyan]")

                # Regenerate with corrections
                correction_prompt = f"""
原始内容存在以下问题：
{chr(10).join(f"- {issue['description']}" for issue in verification['issues'])}

请修正这些问题，重新生成「{chapter.title}」的内容。
保持原有结构（三视角 + 例子），但确保事实准确。

用户背景：{session.user_context}
"""
                response = self.llm.chat(
                    messages=[{"role": "user", "content": correction_prompt}],
                    temperature=0.5,
                    max_tokens=6000,
                )

            # Add disclaimer if needed
            if verification.get("disclaimer_needed"):
                console.print(f"\n[dim]ℹ️  {verification['disclaimer_text']}[/dim]\n")

        # Parse and save content
        chapter.content = self._parse_chapter_content(response)
        self.session_manager.save(session)

        # Display content
        self._display_chapter_content(chapter.content)

        return session

    def _spiral_review(self, session: Session, current_chapter_id: int):
        """Spiral review: flashcards from previous chapters.

        Reviews chapter N-1 and N-3 (if they exist) using spaced repetition.
        """
        from rich.prompt import Prompt

        review_ids = []
        if current_chapter_id > 1:
            review_ids.append(current_chapter_id - 1)  # Previous chapter
        if current_chapter_id > 3:
            review_ids.append(current_chapter_id - 3)  # 3 chapters ago

        if not review_ids:
            return

        console.print("\n[cyan]📌 快速回顾（间隔重复）[/cyan]\n")

        for review_id in review_ids:
            review_chapter = session.map.chapters[review_id - 1]

            if not review_chapter.content:
                continue

            console.print(f"[bold]回顾第 {review_id} 章：{review_chapter.title}[/bold]")

            # Generate flashcard
            flashcard_prompt = f"""
章节：{review_chapter.title}
内容摘要：
- 用户视角：{review_chapter.content.user_perspective[:150]}...
- 业务方视角：{review_chapter.content.business_perspective[:150]}...

生成一道简短的回顾题（不要太难，目的是唤醒记忆）：
"""

            flashcard = self.llm.chat(
                messages=[{"role": "user", "content": flashcard_prompt}],
                temperature=0.7,
                max_tokens=200,
            )

            console.print(f"[dim]{flashcard.strip()}[/dim]\n")

            answer = Prompt.ask("[yellow]你的回答（简短即可）[/yellow]", default="跳过")

            if answer.lower() != "跳过":
                # Quick feedback
                feedback_prompt = f"""
问题：{flashcard}
用户答案：{answer}

简短评价（一句话）：对/基本对/需要复习
"""
                feedback = self.llm.chat(
                    messages=[{"role": "user", "content": feedback_prompt}],
                    temperature=0.3,
                    max_tokens=100,
                )
                console.print(f"[dim]💬 {feedback.strip()}[/dim]\n")

        console.print("[cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]\n")

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
    ) -> dict:
        """Evaluate user's answer to a question.

        Returns:
            dict with keys: correct, reasoning_sound, feedback, hint,
                           variant_question, ask_reasoning
        """
        chapter = session.map.chapters[chapter_id - 1]
        question = next((q for q in chapter.quiz if q.id == question_id), None)

        if not question:
            raise ValueError(f"Question {question_id} not found")

        # Increment attempt count
        question.attempt_count += 1

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
        question.reasoning_sound = eval_data.get("reasoning_sound")
        question.feedback = eval_data["feedback"]
        question.hint = eval_data.get("hint")
        question.variant_question = eval_data.get("variant_question")

        self.session_manager.save(session)

        return eval_data
        )

    def _parse_evaluation(self, response: str) -> dict:
        """Parse evaluation result from JSON response."""
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if not json_match:
            raise ValueError("Failed to parse evaluation")

        return json.loads(json_match.group(0))

    def check_chapter_passed(self, session: Session, chapter_id: int) -> bool:
        """Check if all questions in chapter are answered correctly with sound reasoning."""
        chapter = session.map.chapters[chapter_id - 1]
        for q in chapter.quiz:
            if q.correct is None:
                return False  # Not answered yet
            if not q.correct:
                return False  # Wrong answer
            # If reasoning_sound is explicitly False, not passed
            if q.reasoning_sound is False:
                return False
        return True
