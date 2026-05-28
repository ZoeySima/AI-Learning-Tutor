"""CLI interface for AI Learning Tutor."""
import sys
import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table

from .llm import LLMClient
from .core import MapPhase, LearnPhase, QuizPhase
from .state import SessionManager

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """AI Learning Tutor - 用 AI 重新定义学习"""
    pass


@main.command()
@click.argument("topic")
def start(topic: str):
    """开始新的学习会话

    示例：ai-tutor start "区块链技术基础"
    """
    console.print("\n[bold cyan]欢迎使用 AI Learning Tutor！[/bold cyan]\n")

    # Get user context
    user_context = Prompt.ask(
        "[yellow]请简单介绍你的背景（职业、已有知识）[/yellow]"
    )

    if not user_context.strip():
        console.print("[red]背景信息不能为空[/red]")
        sys.exit(1)

    try:
        # Initialize
        llm = LLMClient()
        session_manager = SessionManager()

        # Create session
        session = session_manager.create(topic, user_context)
        console.print(f"\n[green]✓ 创建会话：{session.session_id}[/green]")

        # Generate map
        map_phase = MapPhase(llm, session_manager)
        session = map_phase.generate_outline(session)

        # Start learning loop
        _learning_loop(session, llm, session_manager)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]学习已暂停。使用 'ai-tutor resume' 继续。[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]错误：{e}[/red]")
        sys.exit(1)


@main.command()
@click.argument("session_id")
def resume(session_id: str):
    """恢复已有学习会话

    示例：ai-tutor resume 20260527-blockchain
    """
    try:
        llm = LLMClient()
        session_manager = SessionManager()

        session = session_manager.load(session_id)
        console.print(f"\n[green]✓ 恢复会话：{session.topic}[/green]")

        if session.status == "completed":
            console.print("[yellow]该会话已完成！[/yellow]")
            if Confirm.ask("要导出学习笔记吗？"):
                markdown = session_manager.export_markdown(session_id)
                console.print(markdown)
            return

        _learning_loop(session, llm, session_manager)

    except FileNotFoundError:
        console.print(f"[red]会话 {session_id} 不存在[/red]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n\n[yellow]学习已暂停。使用 'ai-tutor resume' 继续。[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]错误：{e}[/red]")
        sys.exit(1)


@main.command("list")
def list_sessions():
    """列出所有学习会话"""
    session_manager = SessionManager()
    sessions = session_manager.list_sessions()

    if not sessions:
        console.print("[yellow]还没有任何学习会话[/yellow]")
        return

    table = Table(title="学习会话列表")
    table.add_column("会话 ID", style="cyan")
    table.add_column("主题", style="green")
    table.add_column("状态", style="yellow")
    table.add_column("创建时间", style="blue")

    for s in sessions:
        table.add_row(
            s["session_id"],
            s["topic"],
            s["status"],
            s["created_at"][:10],
        )

    console.print(table)


@main.command()
@click.argument("session_id")
@click.option("--output", "-o", help="输出文件路径（默认输出到终端）")
def export(session_id: str, output: str = None):
    """导出学习笔记为 Markdown

    示例：ai-tutor export 20260527-blockchain -o notes.md
    """
    try:
        session_manager = SessionManager()
        markdown = session_manager.export_markdown(session_id)

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(markdown)
            console.print(f"[green]✓ 已导出到 {output}[/green]")
        else:
            console.print(markdown)

    except FileNotFoundError:
        console.print(f"[red]会话 {session_id} 不存在[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]错误：{e}[/red]")
        sys.exit(1)


def _learning_loop(session, llm, session_manager):
    """Main learning loop: Learn → Quiz → Next chapter."""
    learn_phase = LearnPhase(llm, session_manager)
    quiz_phase = QuizPhase(llm, session_manager)

    # Find next chapter to learn
    next_chapter_id = session.current_chapter_id or 1

    for chapter in session.map.chapters[next_chapter_id - 1:]:
        if chapter.status == "completed":
            continue

        # Teach chapter
        Prompt.ask(f"\n[yellow]准备好了吗？按回车开始第 {chapter.id} 章[/yellow]", default="")
        session = learn_phase.teach_chapter(session, chapter.id)

        # Quiz
        Prompt.ask("\n[yellow]理解了吗？按回车进入测验[/yellow]", default="")
        session = quiz_phase.generate_questions(session, chapter.id)

        # Ask questions
        all_correct = False
        while not all_correct:
            for i, question in enumerate(chapter.quiz, 1):
                if question.correct:
                    continue  # Skip already correct answers

                console.print(f"\n[bold]问题 {i}/{len(chapter.quiz)}：[/bold]")
                console.print(question.question)
                console.print()

                user_answer = Prompt.ask("[yellow]你的答案[/yellow]")

                correct, feedback, hint = quiz_phase.evaluate_answer(
                    session, chapter.id, question.id, user_answer
                )

                if correct:
                    console.print(f"\n[green]✅ {feedback}[/green]\n")
                else:
                    console.print(f"\n[red]❌ {feedback}[/red]")
                    if hint:
                        console.print(f"[yellow]💡 提示：{hint}[/yellow]\n")

            # Check if all passed
            all_correct = quiz_phase.check_chapter_passed(session, chapter.id)

            if not all_correct:
                if not Confirm.ask("\n[yellow]有题目答错了，要重新作答吗？[/yellow]"):
                    console.print("[yellow]学习已暂停。使用 'ai-tutor resume' 继续。[/yellow]")
                    return

        # Mark chapter as completed
        chapter.status = "completed"
        chapter.quiz_passed = True
        session_manager.save(session)

        console.print(f"\n[green]🎉 第 {chapter.id} 章通过！[/green]")

    # All chapters completed
    session.status = "completed"
    session_manager.save(session)

    console.print("\n[bold green]🎊 恭喜！你已完成所有章节的学习！[/bold green]\n")
    if Confirm.ask("要导出学习笔记吗？"):
        markdown = session_manager.export_markdown(session.session_id)
        filename = f"{session.session_id}-notes.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(markdown)
        console.print(f"[green]✓ 已导出到 {filename}[/green]")


if __name__ == "__main__":
    main()
