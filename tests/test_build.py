"""Tests for the solution.txt builder (TDD — written first)."""

import pytest

from src.build import build_lines, load_magic_word
from src.prompts import PROMPTS
from src.validate import validate_solution

# A realistic 17-31-byte stand-in for the recovered magic word.
SYNTHETIC_WORD = "synthetic-word-1234567890"


def test_build_lines_shape():
    lines = build_lines(SYNTHETIC_WORD)
    assert len(lines) == 10, f"expected 10 lines, got {len(lines)}"
    # Line 1 is the magic word byte-for-byte (no strip/case/normalization).
    assert lines[0] == SYNTHETIC_WORD
    # Lines 2-10 are the prompt texts in PROMPTS order.
    assert lines[1:] == [p.text for p in PROMPTS]


def test_build_lines_passes_validator():
    # Catches near-duplicates between the word and prompt lines and any
    # length violations, using the same gate the contest deliverable faces.
    assert validate_solution(build_lines(SYNTHETIC_WORD)) == []


def test_build_lines_refuses_empty():
    for bad in ("", "   ", "  \t  "):
        with pytest.raises(ValueError):
            build_lines(bad)


def test_load_magic_word_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_magic_word(tmp_path / "nope.txt")


def test_load_magic_word_rejects_embedded_newline(tmp_path):
    path = tmp_path / "magic_word.txt"
    path.write_text("line one\nline two\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_magic_word(path)
    # A verbatim word (exactly as cracker.py writes it) round-trips untouched.
    good = tmp_path / "good.txt"
    good.write_text(SYNTHETIC_WORD, encoding="utf-8")
    assert load_magic_word(good) == SYNTHETIC_WORD
