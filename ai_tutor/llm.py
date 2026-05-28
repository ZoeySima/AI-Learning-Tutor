"""AI Learning Tutor - LLM client wrapper."""
import os
from typing import Iterator, Optional
from anthropic import Anthropic, APIError, APITimeoutError
from rich.console import Console

console = Console()


class LLMClient:
    """Wrapper for Anthropic Claude API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-opus-4-7"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Set it via environment variable or pass to constructor."
            )
        self.model = model
        self.client = Anthropic(api_key=self.api_key)

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

