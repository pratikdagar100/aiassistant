"""Settings API: startup behavior (spec section 44) and other runtime-mutable
settings, stored in the `settings` table — config/settings.json stays the
source of truth for infra config (ports, model paths) that isn't meant to
change from the UI.
"""

from __future__ import annotations

import subprocess

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import get_db
from app.db.models import SettingRecord

router = APIRouter()

MUTABLE_KEYS = {
    "startup_enabled": False,
    "auto_select_entity": True,
    "auto_mic": False,
    "wake_word": False,
    "auto_avatar": False,
    "default_entity": "friday",
}


class UpdateSettingsRequest(BaseModel):
    values: dict


def _is_startup_task_registered() -> bool:
    try:
        proc = subprocess.run(
            ["schtasks", "/query", "/tn", "PratikAI"], capture_output=True, text=True, timeout=5
        )
        return proc.returncode == 0
    except Exception:  # noqa: BLE001
        return False


@router.get("")
def get_settings_values(db: Session = Depends(get_db)) -> dict:
    values = dict(MUTABLE_KEYS)
    rows = db.query(SettingRecord).filter(SettingRecord.key.in_(MUTABLE_KEYS.keys())).all()
    for row in rows:
        if row.value is not None:
            values[row.key] = row.value.get("value")

    values["startup_task_registered"] = _is_startup_task_registered()
    values["app_version"] = get_settings().version
    values["phase"] = get_settings().phase
    return values


@router.patch("")
def update_settings_values(req: UpdateSettingsRequest, db: Session = Depends(get_db)) -> dict:
    for key, value in req.values.items():
        if key not in MUTABLE_KEYS:
            continue
        row = db.query(SettingRecord).filter_by(key=key).first()
        if row:
            row.value = {"value": value}
        else:
            db.add(SettingRecord(key=key, value={"value": value}))
    db.commit()
    return get_settings_values(db)
