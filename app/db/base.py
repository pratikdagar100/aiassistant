"""SQLAlchemy declarative base shared by all PratikAI models."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
