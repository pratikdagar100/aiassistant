"""Turns a natural-language task request into a concrete step list, using
the entity's own LLM with constrained JSON output (same technique as
app/memory/extractor.py). The model is shown the actual tool registry so it
can't invent tools that don't exist.
"""

from __future__ import annotations

import json

from app.computer.registry import TOOL_REGISTRY
from app.core.logging import get_logger
from app.entities.loader import EntityProfile
from app.llm.ollama import OllamaClient, OllamaError
from app.security.command_policy import get_policy

logger = get_logger("core.planner")


class PlanningError(RuntimeError):
    pass


def _tool_catalog() -> str:
    lines = []
    for name in TOOL_REGISTRY:
        policy = get_policy(name)
        lines.append(f"- {name}: {policy.reason} (risk: {policy.risk})")
    return "\n".join(lines)


def _system_prompt() -> str:
    return f"""You are a task planner for a computer-use AI agent. Given a user's request,
produce a short, concrete, ordered list of steps using ONLY the tools below. Each step
must specify the exact tool name and the parameters it needs. Prefer the fewest steps
that accomplish the goal. If the request doesn't need any tools (pure conversation),
return an empty steps list.

Available tools:
{_tool_catalog()}

Respond with strict JSON only, matching this shape:
{{"steps": [{{"description": "short human-readable description", "tool": "exact.tool_name", "parameters": {{}}}}]}}
"""


async def generate_plan(entity: EntityProfile, request: str, context: str | None = None) -> list[dict]:
    client = OllamaClient()
    if not await client.is_available():
        raise PlanningError("Ollama is not reachable")

    user_content = request if not context else f"{request}\n\nAdditional context:\n{context}"

    try:
        result = await client.chat(
            model=entity.model,
            messages=[
                {"role": "system", "content": _system_prompt()},
                {"role": "user", "content": user_content},
            ],
            format="json",
        )
    except OllamaError as exc:
        raise PlanningError(f"Planning call failed: {exc}") from exc

    raw = result.get("message", {}).get("content", "")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PlanningError(f"Planner returned non-JSON: {raw[:300]!r}") from exc

    steps = parsed.get("steps", [])
    for step in steps:
        if "tool" not in step or step["tool"] not in TOOL_REGISTRY:
            raise PlanningError(f"Planner produced an invalid tool: {step.get('tool')!r}")
        step.setdefault("parameters", {})
        step.setdefault("description", step["tool"])

    return steps
