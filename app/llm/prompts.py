"""Message-list construction for the Ollama chat API.

Phase 2: plain sliding-window history, no retrieval. Phase 4 (memory) will
extend this to splice in retrieved semantic/episodic memories rather than
sending the entire conversation — see the "do not inject the entire
conversation history into every LLM request" requirement in the spec.
"""

from __future__ import annotations

from app.db.models import KnowledgeChunk, Memory, Message

MAX_HISTORY_MESSAGES = 20  # sliding window — recency; memories/knowledge below cover relevance


def _format_memories(memories: list[Memory]) -> str:
    lines = [f"- {m.content}" for m in memories]
    return "Relevant memories about this user (use only if applicable, don't recite them verbatim):\n" + "\n".join(lines)


def _format_knowledge(chunks: list[KnowledgeChunk]) -> str:
    lines = [f"- {c.content}" for c in chunks]
    return "Relevant excerpts from the entity's knowledge base (cite naturally, don't dump verbatim):\n" + "\n".join(lines)


def build_messages(
    system_prompt: str | None,
    history: list[Message],
    new_message: str,
    memories: list[Memory] | None = None,
    knowledge_chunks: list[KnowledgeChunk] | None = None,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if memories:
        messages.append({"role": "system", "content": _format_memories(memories)})
    if knowledge_chunks:
        messages.append({"role": "system", "content": _format_knowledge(knowledge_chunks)})

    for msg in history[-MAX_HISTORY_MESSAGES:]:
        if msg.role in ("user", "assistant"):
            messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": new_message})
    return messages
