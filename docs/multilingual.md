# Multilingual

## What's implemented

- **Automatic language detection** on every spoken utterance via faster-whisper
  (`app/speech/stt.py`) — the user never selects a language first.
- The LLM (Qwen3 8B) receives text directly in whatever language it's in —
  PratikAI does not auto-translate to English first, per the spec's explicit
  requirement. Language switching mid-conversation works because each turn
  is independently detected and passed through as-is.
- `app/speech/language.py` prioritizes English, Hindi, Punjabi, Bengali,
  Gujarati, Marathi, Tamil, Telugu, Kannada, Malayalam, Urdu, Nepali for
  display purposes — Whisper itself supports more.

## Known limitation: Hinglish

Whisper has no distinct language code for romanized Hindi/English
code-switching ("Hinglish"). Such utterances get classified as `hi` or `en`
depending on which dominates — this is a Whisper limitation, not something
PratikAI corrects. Qwen3 generally still understands Hinglish text
reasonably well even when the detected language label is imprecise, since
the *text itself* (not just the label) goes to the LLM.

## Not implemented

- Google Cloud Speech-to-Text / Translation (hybrid/high-accuracy mode) —
  the `speech.stt_mode` config option supports `google`/`hybrid` values but
  only `local` has a working code path. See `app/speech/stt.py`.
- Per-language TTS voice auto-selection — only one Piper voice
  (`en_US-lessac-medium`) ships by default; see docs/speech.md for adding
  more.
