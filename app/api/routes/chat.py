"""Chat endpoints: send a message, get a reply, persist the conversation.

Phase 4 adds memory: relevant past memories are retrieved and injected into
the system prompt (not the whole conversation history), and each user
message is screened by app.memory.extractor for anything worth remembering
long-term. Phase 5/6/8 still to come: multilingual detection, tool use,
planning.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.database import get_db, session_scope
from app.db.models import Conversation, Entity, Message
from app.llm.model_manager import get_default_model
from app.llm.ollama import OllamaClient, OllamaError
from app.llm.prompts import build_messages
from app.knowledge.retrieval import retrieve_relevant_chunks
from app.memory.extractor import classify_and_store
from app.memory.learning import detect_and_queue
from app.memory.retrieval import retrieve_relevant_memories

router = APIRouter()
logger = get_logger("api.chat")


class ChatRequest(BaseModel):
    message: str
    entity_id: str = "friday"
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    model: str


def _get_or_create_conversation(db: Session, entity_id: str, conversation_id: int | None) -> Conversation:
    if conversation_id is not None:
        convo = db.get(Conversation, conversation_id)
        if not convo or convo.entity_id != entity_id:
            raise HTTPException(404, f"Conversation {conversation_id} not found for entity {entity_id}")
        return convo

    convo = Conversation(entity_id=entity_id)
    db.add(convo)
    db.flush()
    return convo


async def _extract_memory_background(entity_id: str, model: str, user_message: str, conversation_id: int) -> None:
    """Runs after the response is already sent — extraction latency should
    never delay the reply the user is waiting for."""
    try:
        with session_scope() as db:
            await classify_and_store(
                db,
                entity_id=entity_id,
                model=model,
                user_message=user_message,
                conversation_id=conversation_id,
            )
    except Exception:  # noqa: BLE001
        logger.warning("Background memory extraction failed", exc_info=True)


async def _detect_learning_signal_background(
    entity_id: str, model: str, conversation_id: int, prior_reply: str, user_message: str
) -> None:
    try:
        with session_scope() as db:
            await detect_and_queue(
                db,
                entity_id=entity_id,
                model=model,
                conversation_id=conversation_id,
                prior_assistant_reply=prior_reply,
                user_message=user_message,
            )
    except Exception:  # noqa: BLE001
        logger.warning("Background learning-signal detection failed", exc_info=True)


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> ChatResponse:
    entity = db.get(Entity, req.entity_id)
    if not entity:
        raise HTTPException(404, f"Entity '{req.entity_id}' not found")

    convo = _get_or_create_conversation(db, req.entity_id, req.conversation_id)
    history = list(convo.messages)

    model = entity.model or get_default_model()

    memories = []
    if entity.memory_enabled:
        memories = retrieve_relevant_memories(db, req.entity_id, req.message)
    knowledge_chunks = retrieve_relevant_chunks(db, req.entity_id, req.message)

    messages = build_messages(entity.system_prompt, history, req.message, memories, knowledge_chunks)

    client = OllamaClient()
    if not await client.is_available():
        raise HTTPException(503, "Ollama is not reachable. Start it and retry — see docs/troubleshooting.md.")

    user_msg = Message(conversation_id=convo.id, role="user", content=req.message)
    db.add(user_msg)
    db.flush()

    try:
        result = await client.chat(model=model, messages=messages)
    except OllamaError as exc:
        raise HTTPException(502, str(exc)) from exc

    reply_text = result.get("message", {}).get("content", "")
    assistant_msg = Message(conversation_id=convo.id, role="assistant", content=reply_text)
    db.add(assistant_msg)
    db.commit()

    entity.last_active_at = assistant_msg.created_at
    db.commit()

    if entity.memory_enabled:
        background_tasks.add_task(_extract_memory_background, req.entity_id, model, req.message, convo.id)

    prior_assistant_msg = next((m for m in reversed(history) if m.role == "assistant"), None)
    if prior_assistant_msg:
        background_tasks.add_task(
            _detect_learning_signal_background,
            req.entity_id,
            model,
            convo.id,
            prior_assistant_msg.content,
            req.message,
        )

    return ChatResponse(conversation_id=convo.id, reply=reply_text, model=model)


@router.get("/conversations")
def list_conversations(entity_id: str = "friday", db: Session = Depends(get_db)) -> list[dict]:
    convos = db.query(Conversation).filter_by(entity_id=entity_id).order_by(Conversation.started_at.desc()).all()
    return [
        {"id": c.id, "title": c.title, "started_at": c.started_at.isoformat(), "message_count": len(c.messages)}
        for c in convos
    ]


@router.get("/conversations/{conversation_id}/messages")
def get_messages(conversation_id: int, db: Session = Depends(get_db)) -> list[dict]:
    convo = db.get(Conversation, conversation_id)
    if not convo:
        raise HTTPException(404, f"Conversation {conversation_id} not found")
    return [
        {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in convo.messages
    ]


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket) -> None:
    """Streaming chat over WebSocket: client sends {entity_id, conversation_id?, message},
    server streams {type: "chunk", text} events followed by {type: "done", conversation_id}.
    """
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
                req = ChatRequest(**payload)
            except Exception as exc:  # noqa: BLE001
                await websocket.send_json({"type": "error", "detail": f"Invalid request: {exc}"})
                continue

            with session_scope() as db:
                entity = db.get(Entity, req.entity_id)
                if not entity:
                    await websocket.send_json({"type": "error", "detail": f"Entity '{req.entity_id}' not found"})
                    continue

                convo = _get_or_create_conversation(db, req.entity_id, req.conversation_id)
                history = list(convo.messages)
                model = entity.model or get_default_model()

                memories = retrieve_relevant_memories(db, req.entity_id, req.message) if entity.memory_enabled else []
                knowledge_chunks = retrieve_relevant_chunks(db, req.entity_id, req.message)
                messages = build_messages(entity.system_prompt, history, req.message, memories, knowledge_chunks)

                db.add(Message(conversation_id=convo.id, role="user", content=req.message))
                db.flush()
                conversation_id = convo.id
                memory_enabled = entity.memory_enabled

            client = OllamaClient()
            if not await client.is_available():
                await websocket.send_json({"type": "error", "detail": "Ollama is not reachable"})
                continue

            full_reply = []
            try:
                async for chunk in client.chat_stream(model=model, messages=messages):
                    full_reply.append(chunk)
                    await websocket.send_json({"type": "chunk", "text": chunk})
            except OllamaError as exc:
                await websocket.send_json({"type": "error", "detail": str(exc)})
                continue

            with session_scope() as db:
                db.add(
                    Message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content="".join(full_reply),
                    )
                )

            await websocket.send_json({"type": "done", "conversation_id": conversation_id})

            if memory_enabled:
                import asyncio

                asyncio.create_task(
                    _extract_memory_background(req.entity_id, model, req.message, conversation_id)
                )
    except WebSocketDisconnect:
        logger.info("Chat WebSocket disconnected")
