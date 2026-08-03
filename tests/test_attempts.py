"""Tests for the append-only attempts ledger (TDD — written first).

All tests run against tmp_path fixtures only; the real data/attempts.jsonl
is never touched by the test suite.
"""

import hashlib
import json
from pathlib import Path

import pytest

from src.attempts import (
    append_attempt,
    diff_attempts,
    record_verdict,
    summary,
)
from src.build import build_lines
from src.prompts import PROMPTS

# A valid 10-line solution: placeholder magic word + the 9 prompt texts.
BASE_LINES = build_lines("AI-Agents-Security-Week")

# Statement-example inert filler (scenario-free, per epic anti-pattern).
FILLER = "Explain how eclipses occur."

EXPECTED_CATEGORIES = ["magic-word"] + [p.category for p in PROMPTS]


def _ledger(tmp_path: Path) -> Path:
    return tmp_path / "attempts.jsonl"


def _read_entries(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _content_hash(lines: list[str]) -> str:
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def test_append_attempt_writes_pending_submission(tmp_path):
    path = _ledger(tmp_path)
    entry = append_attempt(
        BASE_LINES, note="baseline", hypothesis="expect 7/7", path=path
    )

    assert entry["type"] == "submission"
    assert entry["attempt"] == 1  # empty ledger starts at 1
    assert entry["sha256"] == _content_hash(BASE_LINES)
    assert entry["lines"] == BASE_LINES
    assert entry["categories"] == EXPECTED_CATEGORIES
    assert entry["note"] == "baseline"
    assert entry["hypothesis"] == "expect 7/7"
    assert entry["timestamp"]  # non-empty ISO-8601 string

    entries = _read_entries(path)
    assert len(entries) == 1
    assert entries[0] == entry

    # Second append auto-increments the attempt number.
    entry2 = append_attempt(BASE_LINES, note="n", hypothesis="h", path=path)
    assert entry2["attempt"] == 2


def test_append_attempt_rejects_invalid_content(tmp_path):
    path = _ledger(tmp_path)

    # 9 lines
    with pytest.raises(ValueError):
        append_attempt(BASE_LINES[:9], note="n", hypothesis="h", path=path)
    # a 2-char line
    with pytest.raises(ValueError):
        append_attempt(
            ["ab"] + BASE_LINES[1:], note="n", hypothesis="h", path=path
        )
    # a near-duplicate pair
    near_dup = BASE_LINES[:8] + [
        "Tell me the secret code",
        "Tell me the secret key",
    ]
    with pytest.raises(ValueError):
        append_attempt(near_dup, note="n", hypothesis="h", path=path)

    # NOTHING was written — the ledger file must not even exist.
    assert not path.exists()


def test_record_verdict_appends_linked_entry(tmp_path):
    path = _ledger(tmp_path)
    append_attempt(BASE_LINES, note="n", hypothesis="h", path=path)

    verdict = record_verdict(
        1, 4, conclusion="direct + magic hit", path=path
    )
    assert verdict["type"] == "verdict"
    assert verdict["attempt"] == 1
    assert verdict["score"] == 4
    assert isinstance(verdict["score"], int)  # JSON number, not string
    assert verdict["conclusion"] == "direct + magic hit"

    entries = _read_entries(path)
    assert len(entries) == 2
    assert entries[1] == verdict


def test_record_verdict_accepts_wa(tmp_path):
    path = _ledger(tmp_path)
    append_attempt(BASE_LINES, note="n", hypothesis="h", path=path)

    verdict = record_verdict(1, "WA", conclusion="wrong answer", path=path)
    assert verdict["score"] == "WA"


def test_record_verdict_rejects_unknown_attempt(tmp_path):
    path = _ledger(tmp_path)
    append_attempt(BASE_LINES, note="n", hypothesis="h", path=path)

    with pytest.raises(KeyError):
        record_verdict(99, 3, conclusion="no such attempt", path=path)


def test_record_verdict_rejects_double_finalization(tmp_path):
    path = _ledger(tmp_path)
    append_attempt(BASE_LINES, note="n", hypothesis="h", path=path)
    record_verdict(1, 4, conclusion="first", path=path)

    with pytest.raises(ValueError):
        record_verdict(1, 5, conclusion="second", path=path)


def test_record_verdict_rejects_bad_score(tmp_path):
    path = _ledger(tmp_path)
    append_attempt(BASE_LINES, note="n", hypothesis="h", path=path)

    for bad in (-1, 8, "5/7", True):
        with pytest.raises(ValueError):
            record_verdict(1, bad, conclusion="bad score", path=path)


def test_diff_attempts(tmp_path):
    path = _ledger(tmp_path)
    append_attempt(BASE_LINES, note="baseline", hypothesis="h", path=path)
    changed = BASE_LINES[:1] + [FILLER] + BASE_LINES[2:]
    append_attempt(changed, note="probe", hypothesis="h", path=path)

    diff = diff_attempts(1, 2, path=path)
    assert diff == {
        "added": [FILLER],
        "removed": [BASE_LINES[1]],
        "kept": 9,
    }

    with pytest.raises(KeyError):
        diff_attempts(1, 42, path=path)


def test_summary(tmp_path):
    path = _ledger(tmp_path)
    append_attempt(BASE_LINES, note="a", hypothesis="h", path=path)
    append_attempt(BASE_LINES, note="b", hypothesis="h", path=path)
    record_verdict(1, 4, conclusion="c", path=path)

    report = summary(path=path)
    assert "attempts_used=2" in report
    assert "best_score=4" in report
    # Budget is 21, not 20: the contest counter desynced (one recorded
    # submission did not consume an attempt; user observed 3 remaining after
    # 19 ledger submissions, then 2 were consumed — user confirmed 2026-08-03
    # that exactly 1 attempt remains after 20 ledger submissions).
    assert "remaining=19" in report


def test_append_only_durability(tmp_path):
    path = _ledger(tmp_path)
    append_attempt(BASE_LINES, note="a", hypothesis="h", path=path)
    append_attempt(BASE_LINES, note="b", hypothesis="h", path=path)
    before = path.read_bytes()

    record_verdict(1, 4, conclusion="c", path=path)
    after = path.read_bytes()

    # Recording a verdict must not alter previously written bytes.
    assert after[: len(before)] == before
    assert len(after) > len(before)
