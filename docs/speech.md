# Speech (Phase 5)

## STT — faster-whisper

Runs entirely locally, CPU by default (`speech.whisper_device` in
`config/settings.json`) so it never competes with the LLM for VRAM. The
model (`small` by default) downloads automatically on first use via
Hugging Face Hub and is cached under the venv's huggingface cache.

Language is auto-detected on every utterance — you never pick a language
first. `POST /api/speech/transcribe` (multipart file upload) returns
`{text, language, language_name, language_confidence, engine}`.

Known limitation: Whisper has no separate code for "Hinglish"
(romanized Hindi/English code-switching) — such utterances get classified
as `hi` or `en` depending on which dominates. This is a model limitation,
not something PratikAI can currently correct.

## TTS — Piper (standalone binary, not the PyPI package)

`pip install piper-tts` fails on Windows — its dependency
`piper-phonemize` has no published Windows wheel. PratikAI instead
downloads the official standalone Piper binary and drives it via
subprocess (`app/speech/tts.py`).

Already installed in this repo:
- Binary: `models/piper/piper/piper.exe`
- Voice: `models/piper/voices/en_US-lessac-medium.onnx` (+ `.onnx.json`)

### Installing more voices/languages

Browse available voices at https://huggingface.co/rhasspy/piper-voices/tree/main
(organized by language code, e.g. `hi/`, `pa/`, `bn/`). For each voice you
want, download both files into `models/piper/voices/`:

```powershell
$lang = "hi"; $name = "hi_IN-pratham-medium"  # example — check the repo for actual available names
Invoke-WebRequest "https://huggingface.co/rhasspy/piper-voices/resolve/main/$lang/.../$name.onnx" -OutFile "models\piper\voices\$name.onnx"
Invoke-WebRequest "https://huggingface.co/rhasspy/piper-voices/resolve/main/$lang/.../$name.onnx.json" -OutFile "models\piper\voices\$name.onnx.json"
```

`GET /api/speech/voices` lists everything currently installed. Set
`speech.default_voice` in `config/settings.json`, or pass `voice` per-entity
once the Phase 3 wizard grows a voice-selection step (currently every
entity uses the global default — see docs/entities.md roadmap note).

## Hybrid / Google STT (not yet implemented)

`speech.stt_mode` in config supports `local` (implemented), `google`, and
`hybrid` as documented modes, but only `local` has a working code path so
far — Google Cloud Speech-to-Text integration is deferred; the interface is
shaped so it can be added without changing callers (`app/speech/stt.py`).
