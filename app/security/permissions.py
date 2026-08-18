"""Per-entity permission model (spec section 28).

Permissions are stored as an EntitySettings row (key="permissions") rather
than new columns, since the category list is Windows/computer-use specific
and may grow — adding a category shouldn't require a migration.

Each category maps to one of three modes:
  disabled     — tool calls in this category are rejected outright
  enabled      — tool calls execute immediately
  confirmation — tool calls create a pending approval (spec section 29)
    and only execute once approved via the audit/approval API
"""

from __future__ import annotations

from enum import Enum

from sqlalchemy.orm import Session

from app.db.models import Entity, EntitySettings


class PermissionCategory(str, Enum):
    SCREEN = "SCREEN"
    MOUSE = "MOUSE"
    KEYBOARD = "KEYBOARD"
    CLIPBOARD = "CLIPBOARD"
    APPLICATIONS = "APPLICATIONS"
    FILESYSTEM_READ = "FILESYSTEM_READ"
    FILESYSTEM_WRITE = "FILESYSTEM_WRITE"
    FILESYSTEM_DELETE = "FILESYSTEM_DELETE"
    TERMINAL = "TERMINAL"
    POWERSHELL = "POWERSHELL"
    PYTHON = "PYTHON"
    BROWSER = "BROWSER"
    NETWORK = "NETWORK"
    SYSTEM = "SYSTEM"
    ADMINISTRATOR = "ADMINISTRATOR"


class PermissionMode(str, Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    CONFIRMATION = "confirmation"


# Safe-by-default: everything requires confirmation except pure reads, until
# an entity's computer_access flag is on AND permissions are explicitly
# configured. ADMINISTRATOR is never enabled by default, ever (section 45:
# "never bypass UAC or Windows security mechanisms").
DEFAULT_PERMISSIONS: dict[str, str] = {
    PermissionCategory.SCREEN: PermissionMode.ENABLED,
    PermissionCategory.MOUSE: PermissionMode.CONFIRMATION,
    PermissionCategory.KEYBOARD: PermissionMode.CONFIRMATION,
    PermissionCategory.CLIPBOARD: PermissionMode.CONFIRMATION,
    PermissionCategory.APPLICATIONS: PermissionMode.CONFIRMATION,
    PermissionCategory.FILESYSTEM_READ: PermissionMode.ENABLED,
    PermissionCategory.FILESYSTEM_WRITE: PermissionMode.CONFIRMATION,
    PermissionCategory.FILESYSTEM_DELETE: PermissionMode.CONFIRMATION,
    PermissionCategory.TERMINAL: PermissionMode.CONFIRMATION,
    PermissionCategory.POWERSHELL: PermissionMode.CONFIRMATION,
    PermissionCategory.PYTHON: PermissionMode.CONFIRMATION,
    PermissionCategory.BROWSER: PermissionMode.CONFIRMATION,
    PermissionCategory.NETWORK: PermissionMode.CONFIRMATION,
    PermissionCategory.SYSTEM: PermissionMode.CONFIRMATION,
    PermissionCategory.ADMINISTRATOR: PermissionMode.DISABLED,
}


def get_permissions(db: Session, entity_id: str) -> dict[str, str]:
    row = db.query(EntitySettings).filter_by(entity_id=entity_id, key="permissions").first()
    merged = dict(DEFAULT_PERMISSIONS)
    if row and row.value:
        merged.update(row.value)
    return merged


def set_permissions(db: Session, entity_id: str, permissions: dict[str, str]) -> dict[str, str]:
    for category, mode in permissions.items():
        if category not in PermissionCategory.__members__:
            raise ValueError(f"Unknown permission category '{category}'")
        if mode not in (PermissionMode.DISABLED, PermissionMode.ENABLED, PermissionMode.CONFIRMATION):
            raise ValueError(f"Unknown permission mode '{mode}'")

    row = db.query(EntitySettings).filter_by(entity_id=entity_id, key="permissions").first()
    current = dict(DEFAULT_PERMISSIONS)
    if row and row.value:
        current.update(row.value)
    current.update(permissions)

    if row:
        row.value = current
    else:
        db.add(EntitySettings(entity_id=entity_id, key="permissions", value=current))
    db.flush()
    return current


def get_mode(db: Session, entity_id: str, category: str) -> str:
    entity = db.get(Entity, entity_id)
    if entity and not entity.computer_access:
        return PermissionMode.DISABLED
    return get_permissions(db, entity_id).get(category, PermissionMode.CONFIRMATION)
