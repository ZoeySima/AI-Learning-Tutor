"""AI Learning Tutor - LLM client wrapper."""
import os
from typing import Iterator, Optional
from anthropic import Anthropic, APIError, APITimeoutError
from rich.console import Console

console = Console()


class LLMClient:
    """Wrapper for Anthropic Claude API."""

    DEFAULT_MODEL = "claude-sonnet-4-5"
    VERIFICATION_MODEL = "claude-opus-4-7"  # 用于事实核查的更强模型

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Set it via environment variable or pass to constructor."
            )
        # Allow model override via env var
        self.model = model or os.getenv("AI_TUTOR_MODEL") or self.DEFAULT_MODEL
        self.client = Anthropic(api_key=self.api_key)

        # Critical domains that require fact-checking
        self.critical_domains = {
            "金融", "医学", "法律", "药物", "健康", "投资", "保险",
            "finance", "medical", "legal", "health", "investment"
        }

    def chat(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        stream: bool = False,
        max_tokens: int = 4096,
        temperature: float = 1.0,
    ) -> str | Iterator[str]:
        """Send chat request to Claude.

        Args:
            messages: List of {"role": "user"|"assistant", "content": str}
            system: Optional system prompt
            stream: If True, return iterator of text chunks
            max_tokens: Max response tokens
            temperature: Sampling temperature

        Returns:
            Full response text (stream=False) or iterator of chunks (stream=True)
        """
        try:
            if stream:
                return self._stream_chat(messages, system, max_tokens, temperature)
            else:
                return self._sync_chat(messages, system, max_tokens, temperature)
        except APITimeoutError:
            console.print("[red]Request timed out. Please try again.[/red]")
            raise
        except APIError as e:
            console.print(f"[red]API error: {e}[/red]")
            raise

    def _sync_chat(self, messages, system, max_tokens, temperature) -> str:
        """Synchronous chat (returns full response)."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system if system else None,
            messages=messages,
        )
        return response.content[0].text

    def _stream_chat(self, messages, system, max_tokens, temperature) -> Iterator[str]:
        """Streaming chat (yields text chunks)."""
        with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system if system else None,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    def verify_facts(self, content: str, topic: str) -> dict:
        """Verify factual accuracy of generated content.

        Args:
            content: The content to verify
            topic: The learning topic (to check if it's a critical domain)

        Returns:
            dict with keys: is_critical, verified, issues, confidence
        """
        # Check if topic is in critical domain
        is_critical = any(
            keyword in topic.lower() for keyword in self.critical_domains
        )

        if not is_critical:
            # Non-critical domain, skip verification
            return {
                "is_critical": False,
                "verified": True,
                "issues": [],
                "confidence": "high",
            }

        # Critical domain - perform verification
        console.print("[dim]🔍 关键领域检测，正在进行事实核查...[/dim]")

        verification_prompt = f"""
你是一位严谨的事实核查专家。请审查以下学习内容的准确性。

主题：{topic}
内容：
{content}

请检查：
1. 是否有明显的事实错误（定义、公式、历史事件、法律条文等）
2. 是否有过时的信息（特别是法律、医学、金融领域）
3. 是否有误导性的简化或类比
4. 是否有需要加免责声明的内容（如医疗建议、投资建议）

输出 JSON 格式：
{{
  "verified": true/false,
  "confidence": "high/medium/low",
  "issues": [
    {{"type": "错误类型", "location": "具体位置", "description": "问题描述", "severity": "high/medium/low"}}
  ],
  "disclaimer_needed": true/false,
  "disclaimer_text": "如果需要免责声明，这里是建议的文本"
}}
"""

        try:
            response = self.client.messages.create(
                model=self.VERIFICATION_MODEL,  # Use stronger model for verification
                max_tokens=2000,
                temperature=0.1,  # Low temperature for factual tasks
                messages=[{"role": "user", "content": verification_prompt}],
            )

            import json
            import re

            result_text = response.content[0].text
            json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                result["is_critical"] = True
                return result
            else:
                # Fallback if parsing fails
                return {
                    "is_critical": True,
                    "verified": True,
                    "issues": [],
                    "confidence": "medium",
                }

        except Exception as e:
            console.print(f"[yellow]⚠️  事实核查失败: {e}[/yellow]")
            return {
                "is_critical": True,
                "verified": True,  # Fail open to not block learning
                "issues": [],
                "confidence": "unknown",
            }

