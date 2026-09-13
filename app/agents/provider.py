from __future__ import annotations

import json
import os
from typing import Any, Protocol, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(Protocol):
    def structured(self, system_prompt: str, user_prompt: str, schema: type[T]) -> T: ...


class MockLLMProvider:
    """Safe default: deterministic workflow using local evidence when no key is provided."""

    def structured(self, system_prompt: str, user_prompt: str, schema: type[T]) -> T:
        raise RuntimeError("Mock provider: no LLM key set — agents operate in deterministic mode.")


class OpenAICompatibleProvider:
    """
    Supports both OpenAI API and HuggingFace Inference API (OpenAI-compatible endpoint).

    - OpenAI keys: start with 'sk-'       → base_url = https://api.openai.com/v1
    - HuggingFace keys: start with 'hf_'  → base_url = https://api-inference.huggingface.co/v1
    - Custom base_url via OPENAI_BASE_URL env var overrides all of the above.
    """

    # Default HuggingFace model (free-tier, supports structured JSON output)
    HF_DEFAULT_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
    HF_BASE_URL = "https://api-inference.huggingface.co/v1"
    OPENAI_BASE_URL = "https://api.openai.com/v1"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        env_model = os.getenv("OPENAI_MODEL", "")

        # Detect HuggingFace key
        is_hf_key = self.api_key.startswith("hf_")

        # Resolve base URL
        custom_base = base_url or os.getenv("OPENAI_BASE_URL", "")
        if custom_base:
            self.base_url = custom_base.rstrip("/")
        elif is_hf_key:
            self.base_url = self.HF_BASE_URL
        else:
            self.base_url = self.OPENAI_BASE_URL

        # Resolve model
        if model:
            self.model = model
        elif is_hf_key and (not env_model or env_model == "gpt-4o-mini"):
            # HF can't run GPT models; use a free open model
            self.model = self.HF_DEFAULT_MODEL
        else:
            self.model = env_model or "gpt-4o-mini"

        self.is_hf = is_hf_key

    def structured(self, system_prompt: str, user_prompt: str, schema: type[T]) -> T:
        if not self.api_key or self.api_key.startswith("mock-"):
            raise ValueError("No valid LLM API key configured.")

        try:
            import httpx

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            payload: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1024,
            }

            # HuggingFace supports JSON mode differently — use grammar/schema hint in prompt
            if self.is_hf:
                # Append JSON schema hint to system prompt for HF models
                schema_hint = f"\n\nRespond ONLY with a valid JSON object matching this schema:\n{schema.model_json_schema()}"
                payload["messages"][0]["content"] += schema_hint
            else:
                # OpenAI native JSON mode
                payload["response_format"] = {"type": "json_object"}

            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            response = httpx.post(url, headers=headers, json=payload, timeout=45.0)
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]

            # Extract JSON if wrapped in markdown code fences
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            parsed_json = json.loads(content)
            return schema.model_validate(parsed_json)

        except Exception as e:
            raise RuntimeError(f"LLM structured completion failed ({self.base_url}): {e}") from e


def get_llm_provider() -> LLMProvider:
    """
    Returns the best available LLM provider:
    - hf_* key  → HuggingFace Inference API (free, open models)
    - sk-*  key → OpenAI API
    - anything else / missing → MockLLMProvider (deterministic agents)
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and not api_key.startswith("mock-") and len(api_key) > 10:
        return OpenAICompatibleProvider(api_key=api_key)
    return MockLLMProvider()
