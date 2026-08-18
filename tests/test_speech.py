"""Uses the real Piper binary and real faster-whisper model — no mocking.
Slow on first run (Whisper model download + load) but this is exactly the
kind of thing that's dangerous to fake: a mocked STT/TTS pair would pass
even if the actual audio pipeline were broken.
"""

import pytest

from app.speech import stt, tts


def test_piper_binary_and_voice_available():
    assert tts.piper_binary_available(), "Piper binary missing — see docs/speech.md"
    voices = tts.list_voices()
    assert len(voices) >= 1, "No Piper voices installed — see docs/speech.md"


def test_tts_synthesizes_valid_wav():
    audio = tts.synthesize("This is a test.", voice_name="en_US-lessac-medium")
    assert audio[:4] == b"RIFF"
    assert b"WAVE" in audio[:12]
    assert len(audio) > 1000


def test_tts_unknown_voice_raises():
    with pytest.raises(tts.TTSError):
        tts.synthesize("hello", voice_name="not-a-real-voice")


@pytest.mark.slow
def test_stt_transcribes_tts_output_roundtrip(tmp_path):
    audio = tts.synthesize("The quick brown fox jumps over the lazy dog.", voice_name="en_US-lessac-medium")
    wav_path = tmp_path / "roundtrip.wav"
    wav_path.write_bytes(audio)

    result = stt.transcribe(wav_path)
    assert result.language == "en"
    assert result.language_confidence > 0.5
    # Loose match — Whisper's exact wording can vary slightly (capitalization, punctuation).
    lower = result.text.lower()
    assert "fox" in lower
    assert "dog" in lower
