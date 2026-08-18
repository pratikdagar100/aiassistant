"""Model Manager endpoints (spec section 10/40): list, pull, delete, select default."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.llm.model_manager import list_models, set_default_model, sync_model_record
from app.llm.ollama import OllamaClient, OllamaError

router = APIRouter()


class SelectModelRequest(BaseModel):
    name: str


@router.get("")
async def get_models() -> list[dict]:
    statuses = await list_models()
    return [
        {
            "name": s.name,
            "installed": s.installed,
            "size_bytes": s.size_bytes,
            "parameter_size": s.parameter_size,
            "quantization": s.quantization,
            "is_default": s.is_default,
        }
        for s in statuses
    ]


@router.post("/pull")
async def pull_model(req: SelectModelRequest) -> StreamingResponse:
    """Streams NDJSON progress events while Ollama pulls the model."""
    client = OllamaClient()

    async def event_stream():
        try:
            async for progress in client.pull(req.name):
                yield json.dumps(progress) + "\n"
        except OllamaError as exc:
            yield json.dumps({"error": str(exc)}) + "\n"
            return
        await sync_model_record(req.name)
        yield json.dumps({"status": "complete", "model": req.name}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@router.post("/default")
def select_default_model(req: SelectModelRequest) -> dict:
    set_default_model(req.name)
    return {"default_model": req.name}


@router.delete("/{name}")
async def delete_model(name: str) -> dict:
    client = OllamaClient()
    try:
        await client.delete(name)
    except OllamaError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {"deleted": name}


@router.get("/{name}/test")
async def test_model(name: str) -> dict:
    """Sends a trivial prompt to confirm the model actually responds."""
    client = OllamaClient()
    if not await client.is_available():
        raise HTTPException(503, "Ollama is not reachable")
    try:
        result = await client.chat(model=name, messages=[{"role": "user", "content": "Reply with OK."}])
    except OllamaError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {"model": name, "response": result.get("message", {}).get("content", "")}
