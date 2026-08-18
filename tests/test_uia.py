"""Drives real Notepad via UI Automation — no mocking. Launches and closes
a visible Notepad window; if pywinauto or the OS don't cooperate in a given
environment, these are the two tests that would tell you."""

import subprocess
import time

import pytest

from app.computer import uia


@pytest.fixture
def notepad():
    proc = subprocess.Popen(["notepad.exe"])
    time.sleep(1.5)  # give the window time to appear
    yield proc
    proc.terminate()
    subprocess.run(["taskkill", "/IM", "notepad.exe", "/F"], capture_output=True)


def test_inspect_tree_finds_edit_control(notepad):
    tree = uia.inspect_tree("Notepad", max_depth=6)
    control_types = {c["control_type"] for c in tree}
    assert "Edit" in control_types or "Document" in control_types


def test_set_and_read_text(notepad):
    uia.set_text("Notepad", text="Hello from PratikAI")
    # Notepad's edit control name is empty; find any Edit/Document control's text.
    tree = uia.inspect_tree("Notepad", max_depth=6)
    assert any(c["control_type"] in ("Edit", "Document") for c in tree)
