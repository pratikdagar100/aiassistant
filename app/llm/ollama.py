"""Thin async client for the Ollama HTTP API.

Kept deliberately provider-shaped rather than Ollama-specific in its public
surface (chat/list_models/pull/delete/show) so a different local LLM runtime
could be swapped in later without touching callers — see app/llm/model_manager.py
and app/api/routes/chat.py, which only depend on this interface.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("llm.ollama")


class OllamaError(RuntimeError):
    """Raised when Ollama is unreachable or returns an error."""


class OllamaClient:
    def __init__(self, host: str | None = None, timeout: float = 120.0) -> None:
        self.host = (host or get_settings().llm.ollama_host).rstrip("/")
        self.timeout = timeout

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self.host}/api/version")
                return resp.status_code == 200
        except httpx.RequestError:
            return False

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        stream: bool = False,
        format: str | dict | None = None,
    ) -> dict[str, Any]:
        """Non-streaming chat completion. Returns the parsed final response.

        `format="json"` asks Ollama to constrain output to valid JSON —
        used by app.memory.extractor for reliable structured classification.
        """
        payload: dict[str, Any] = {"model": model, "messages": messages, "stream": False}
        if format is not None:
            payload["format"] = format

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(f"{self.host}/api/chat", json=payload)
            except httpx.RequestError as exc:
                raise OllamaError(f"Could not reach Ollama at {self.host}: {exc}") from exc

        if resp.status_code == 404:
            raise OllamaError(
                f"Model '{model}' is not installed. Pull it with: ollama pull {model}"
            )
        if resp.status_code != 200:
            raise OllamaError(f"Ollama returned {resp.status_code}: {resp.text}")

        return resp.json()

    async def chat_stream(
        self,
        model: str,
        messages: list[dict[str, str]],
    ) -> AsyncIterator[str]:
        """Yields response text chunks as they arrive from Ollama."""
        import json

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.host}/api/chat",
                    json={"model": model, "messages": messages, "stream": True},
                ) as resp:
                    if resp.status_code != 200:
                        body = await resp.aread()
                        raise OllamaError(f"Ollama returned {resp.status_code}: {body!r}")
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if chunk.get("done"):
                            break
            except httpx.RequestError as exc:
                raise OllamaError(f"Could not reach Ollama at {self.host}: {exc}") from exc

    async def list_models(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                resp = await client.get(f"{self.host}/api/tags")
            except httpx.RequestError as exc:
                raise OllamaError(f"Could not reach Ollama at {self.host}: {exc}") from exc
        if resp.status_code != 200:
            raise OllamaError(f"Ollama returned {resp.status_code}: {resp.text}")
        return resp.json().get("models", [])

    async def show(self, model: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                resp = await client.post(f"{self.host}/api/show", json={"model": model})
            except httpx.RequestError as exc:
                raise OllamaError(f"Could not reach Ollama at {self.host}: {exc}") from exc
        if resp.status_code != 200:
            raise OllamaError(f"Model '{model}' not found: {resp.text}")
        return resp.json()

    async def pull(self, model: str) -> AsyncIterator[dict[str, Any]]:
        """Yields progress events while pulling a model."""
        import json

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST", f"{self.host}/api/pull", json={"model": model, "stream": True}
            ) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise OllamaError(f"Pull failed ({resp.status_code}): {body!r}")
                async for line in resp.aiter_lines():
                    if line:
                        yield json.loads(line)

    async def delete(self, model: str) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.request(
                    "DELETE", f"{self.host}/api/delete", json={"model": model}
                )
            except httpx.RequestError as exc:
                raise OllamaError(f"Could not reach Ollama at {self.host}: {exc}") from exc
        if resp.status_code not in (200, 404):
            raise OllamaError(f"Delete failed ({resp.status_code}): {resp.text}")
