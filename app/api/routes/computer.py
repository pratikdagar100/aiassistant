"""Computer control API — every call goes through the approval gateway
(app/security/approval.py) before app/computer/registry.py ever executes
anything. This is the enforcement point for the spec's permission system."""

from __future__ import annotations

import inspect

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.computer.registry import TOOL_REGISTRY, get_tool
from app.core.logging import get_logger
from app.db.database import get_db
from app.security import approval
from app.security.command_policy import get_policy

router = APIRouter()
logger = get_logger("api.computer")


class ExecuteRequest(BaseModel):
    entity_id: str
    tool: str
    parameters: dict = {}
    user_request: str | None = None


async def _run_tool(tool: str, parameters: dict) -> str:
    fn = get_tool(tool)
    result = fn(**parameters)
    if inspect.isawaitable(result):
        result = await result
    return str(result)


@router.get("/tools")
def list_tools() -> list[dict]:
    return [
        {"tool": name, "category": get_policy(name).category, "risk": get_policy(name).risk, "description": get_policy(name).reason}
        for name in TOOL_REGISTRY
    ]


@router.post("/execute")
async def execute(req: ExecuteRequest, db: Session = Depends(get_db)) -> dict:
    if req.tool not in TOOL_REGISTRY:
        raise HTTPException(404, f"Unknown tool '{req.tool}'")

    try:
        entry = approval.request_execution(
            db, entity_id=req.entity_id, tool=req.tool, parameters=req.parameters, user_request=req.user_request
        )
        db.commit()
    except approval.PermissionDenied as exc:
        db.commit()
        raise HTTPException(403, str(exc)) from exc

    if entry.approval_required:
        return {
            "status": "pending_approval",
            "audit_id": entry.id,
            "risk_level": entry.risk_level,
            "tool": req.tool,
            "parameters": req.parameters,
        }

    try:
        result = await _run_tool(req.tool, req.parameters)
        approval.record_result(db, entry.id, result=result, success=True)
        db.commit()
        return {"status": "success", "audit_id": entry.id, "result": result}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Tool execution failed: %s", req.tool, exc_info=True)
        approval.record_result(db, entry.id, result=str(exc), success=False)
        db.commit()
        raise HTTPException(500, f"Tool execution failed: {exc}") from exc


@router.post("/approve/{audit_id}")
async def approve_and_execute(audit_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        entry = approval.approve(db, audit_id)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc

    try:
        result = await _run_tool(entry.tool, entry.parameters or {})
        approval.record_result(db, audit_id, result=result, success=True)
        db.commit()
        return {"status": "success", "audit_id": audit_id, "result": result}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Approved tool execution failed: %s", entry.tool, exc_info=True)
        approval.record_result(db, audit_id, result=str(exc), success=False)
        db.commit()
        raise HTTPException(500, f"Tool execution failed: {exc}") from exc


@router.post("/deny/{audit_id}")
def deny_execution(audit_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        approval.deny(db, audit_id)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc
    return {"status": "denied", "audit_id": audit_id}
