"""Logging setup for PratikAI.

Writes to both the console and a rotating file under data/logs/. Call
configure_logging() once at process startup (app.main does this).
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from app.core.config import get_settings

_CONFIGURED = False


def configure_logging() -> logging.Logger:
    global _CONFIGURED
    settings = get_settings()
    root = logging.getLogger("pratikai")

    if _CONFIGURED:
        return root

    log_dir = settings.logging.resolved_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, settings.logging.level.upper(), logging.INFO)
    root.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    root.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        log_dir / "pratikai.log",
        maxBytes=settings.logging.max_bytes,
        backupCount=settings.logging.backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    root.propagate = False
    _CONFIGURED = True
    return root


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(f"pratikai.{name}")
