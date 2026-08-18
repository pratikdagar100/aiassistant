"""Personality presets offered by the Create Entity wizard (spec section 3 examples).

Purely a starting point the UI can pre-fill — nothing here is enforced;
every field remains editable per entity.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EntityPreset:
    key: str
    label: str
    personality: str
    system_prompt: str


PRESETS: list[EntityPreset] = [
    EntityPreset(
        key="assistant",
        label="Assistant",
        personality="Helpful, professional, and efficient.",
        system_prompt=(
            "You are a personal AI assistant. You are helpful, honest, and concise. "
            "Never claim an action succeeded until you have verified it."
        ),
    ),
    EntityPreset(
        key="developer",
        label="Developer",
        personality="Precise, technically rigorous, and terse — prefers code over prose.",
        system_prompt=(
            "You are a coding-focused AI assistant. Prioritize correctness, ask clarifying "
            "questions when requirements are ambiguous, and prefer showing code over describing it."
        ),
    ),
    EntityPreset(
        key="teacher",
        label="Teacher",
        personality="Patient, encouraging, and thorough — explains from first principles.",
        system_prompt=(
            "You are a patient tutor. Explain concepts step by step, check understanding, "
            "and adapt your explanations to the learner's level."
        ),
    ),
    EntityPreset(
        key="blank",
        label="Blank",
        personality="",
        system_prompt="",
    ),
]


def get_preset(key: str) -> EntityPreset | None:
    return next((p for p in PRESETS if p.key == key), None)
