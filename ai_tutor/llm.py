"""AI Learning Tutor - LLM client wrapper.

Supports two providers:
- anthropic (default): Claude via Anthropic SDK
- deepseek: DeepSeek via OpenAI-compatible SDK

Switch via env var: AI_TUTOR_PROVIDER=deepseek
"""
import os
import json
import re
from typing import Iterator, Optional


class LLMClient:
    """Unified LLM client supporting Anthropic and OpenAI-compatible APIs."""

    # Anthropic defaults
    ANTHROPIC_DEFAULT_MODEL = "claude-sonnet-4-5"
    ANTHROPIC_VERIFICATION_MODEL = "claude-opus-4-7"

    # DeepSeek defaults (OpenAI-compatible)
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    DEEPSEEK_DEFAULT_MODEL = "deepseek-chat"
    DEEPSEEK_VERIFICATION_MODEL = "deepseek-reasoner"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        self.provider = (
            provider
            or os.getenv("AI_TUTOR_PROVIDER")
            or self._auto_detect_provider()
        ).lower()

        if self.provider == "deepseek":
            self._init_deepseek(api_key, model)
        elif self.provider == "anthropic":
            self._init_anthropic(api_key, model)
        else:
            raise ValueError(
                f"Unsupported provider: {self.provider}. "
                "Use 'anthropic' or 'deepseek'."
            )

        self.critical_domains = {
            "金融", "医学", "法律", "药物", "健康", "投资", "保险",
            "finance", "medical", "legal", "health", "investment"
        }

    @staticmethod
    def _auto_detect_provider() -> str:
        """Auto-detect provider based on which env var is set."""
        if os.getenv("DEEPSEEK_API_KEY"):
            return "deepseek"
        if os.getenv("ANTHROPIC_API_KEY"):
            return "anthropic"
        return "deepseek"  # default

    def _init_deepseek(self, api_key, model):
        """Initialize DeepSeek client (OpenAI-compatible)."""
        from openai import OpenAI

        self.api_key = (
            api_key
            or os.getenv("DEEPSEEK_API_KEY")
            or os.getenv("ANTHROPIC_API_KEY")  # fallback for compat
        )
        if not self.api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY not found. "
                "Set it via environment variable or pass to constructor."
            )
        self.model = model or os.getenv("AI_TUTOR_MODEL") or self.DEEPSEEK_DEFAULT_MODEL
        self.verification_model = (
            os.getenv("AI_TUTOR_VERIFICATION_MODEL") or self.DEEPSEEK_VERIFICATION_MODEL
        )
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=os.getenv("DEEPSEEK_BASE_URL", self.DEEPSEEK_BASE_URL),
        )

    def _init_anthropic(self, api_key, model):
        """Initialize Anthropic client."""
        from anthropic import Anthropic

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Set it via environment variable or pass to constructor."
            )
        self.model = model or os.getenv("AI_TUTOR_MODEL") or self.ANTHROPIC_DEFAULT_MODEL
        self.verification_model = (
            os.getenv("AI_TUTOR_VERIFICATION_MODEL") or self.ANTHROPIC_VERIFICATION_MODEL
        )
        self.client = Anthropic(api_key=self.api_key)

    # --- Public chat API (provider-agnostic) ---

    def chat(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        stream: bool = False,
        max_tokens: int = 4096,
        temperature: float = 1.0,
    ):
        """Send chat request. Returns str (stream=False) or Iterator[str] (stream=True)."""
        if stream:
            return self._stream_chat(messages, system, max_tokens, temperature)
        return self._sync_chat(messages, system, max_tokens, temperature)

    def _sync_chat(self, messages, system, max_tokens, temperature) -> str:
        if self.provider == "deepseek":
            full_messages = (
                [{"role": "system", "content": system}] if system else []
            )
            full_messages.extend(messages)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content
        else:  # anthropic
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system if system else None,
                messages=messages,
            )
            return response.content[0].text

    def _stream_chat(self, messages, system, max_tokens, temperature) -> Iterator[str]:
        if self.provider == "deepseek":
            full_messages = (
                [{"role": "system", "content": system}] if system else []
            )
            full_messages.extend(messages)
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:  # anthropic
            with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system if system else None,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield text

    # --- Fact verification ---

    def verify_facts(self, content: str, topic: str) -> dict:
        """Verify factual accuracy of generated content."""
        is_critical = any(
            keyword in topic.lower() for keyword in self.critical_domains
        )

        if not is_critical:
            return {
                "is_critical": False,
                "verified": True,
                "issues": [],
                "confidence": "high",
            }

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

输出 JSON 格式（不要任何其他文字）：
{{
  "verified": true,
  "confidence": "high",
  "issues": [],
  "disclaimer_needed": false,
  "disclaimer_text": ""
}}
"""

        try:
            # Use verification_model (more capable) for fact-checking
            saved_model = self.model
            self.model = self.verification_model
            try:
                result_text = self._sync_chat(
                    messages=[{"role": "user", "content": verification_prompt}],
                    system=None,
                    max_tokens=2000,
                    temperature=0.1,
                )
            finally:
                self.model = saved_model

            json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                result["is_critical"] = True
                return result
            return {
                "is_critical": True,
                "verified": True,
                "issues": [],
                "confidence": "medium",
            }
        except Exception as e:
            print(f"Warning: fact-check failed: {e}")
            return {
                "is_critical": True,
                "verified": True,
                "issues": [],
                "confidence": "unknown",
            }
