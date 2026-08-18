"""Language code -> display name, prioritizing the languages the spec calls
out explicitly (section 6). Whisper's detector returns ISO 639-1 codes; it
has no separate code for "Hinglish" (romanized Hindi/English code-switching)
— such utterances typically get detected as "hi" or "en" depending on the
dominant script/words. That's a real limitation, not a bug to silently
paper over — see docs/multilingual.md.
"""

from __future__ import annotations

PRIORITY_LANGUAGES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "pa": "Punjabi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "ur": "Urdu",
    "ne": "Nepali",
}


def display_name(code: str) -> str:
    return PRIORITY_LANGUAGES.get(code, code.upper())


def is_priority_language(code: str) -> bool:
    return code in PRIORITY_LANGUAGES
