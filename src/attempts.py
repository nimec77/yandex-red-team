"""Append-only JSONL ledger for the 20-attempt contest budget.

Two entry types, never rewriting past lines:
- ``submission`` (pending): attempt number, UTC ISO-8601 timestamp, sha256 of
  the exact submitted bytes ('\\n'.join(lines) + '\\n', UTF-8), the raw lines,
  per-line category labels, a note, and a hypothesis (recorded BEFORE the
  submission — a probe without a prediction wastes an attempt).
- ``verdict`` (finalizes a submission): attempt reference, timestamp, score
  (int 0-7 or the string 'WA'), and a conclusion attributing the result.

Every submission is gated through ``src.validate.validate_solution`` — content
that violates the contest constraints is rejected before it can pollute the
ledger. Verdicts are appended as separate lines; prior entries are immutable.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from src.prompts import PROMPTS
from src.validate import validate_solution

ATTEMPT_BUDGET = 20
DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "attempts.jsonl"

_PROMPT_CATEGORY_BY_TEXT = {p.text: p.category for p in PROMPTS}


def _categorize(lines: list[str]) -> list[str]:
    """Label each line: known prompt category, 'magic-word' for line 1, or
    'probe:<first 24 chars>' for anything unmatched."""
    labels = []
    for i, line in enumerate(lines):
        if line in _PROMPT_CATEGORY_BY_TEXT:
            labels.append(_PROMPT_CATEGORY_BY_TEXT[line])
        elif i == 0:
            labels.append("magic-word")
        else:
            labels.append(f"probe:{line[:24]}")
    return labels


def _content_hash(lines: list[str]) -> str:
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_entries(path: Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _append_entry(path: Path, entry: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_attempt(
    lines: list[str],
    note: str,
    hypothesis: str,
    path: Path = DEFAULT_PATH,
) -> dict:
    """Validate and record a pending submission. Raises ValueError (writing
    nothing) if the content violates the contest constraints."""
    violations = validate_solution(lines)
    if violations:
        raise ValueError(
            "refusing to record invalid content: " + "; ".join(violations)
        )

    entries = _load_entries(path)
    submissions = [e for e in entries if e["type"] == "submission"]
    attempt = max((e["attempt"] for e in submissions), default=0) + 1

    entry = {
        "type": "submission",
        "attempt": attempt,
        "timestamp": _now(),
        "sha256": _content_hash(lines),
        "lines": list(lines),
        "categories": _categorize(lines),
        "note": note,
        "hypothesis": hypothesis,
    }
    _append_entry(path, entry)
    return entry


def record_verdict(
    attempt: int,
    score: int | str,
    conclusion: str,
    path: Path = DEFAULT_PATH,
) -> dict:
    """Finalize a pending submission with the pasted contest verdict.

    Raises KeyError if no submission exists for ``attempt`` and ValueError if
    the attempt is already finalized or the score is not int 0-7 or 'WA'.
    """
    # bool is a subclass of int — reject it explicitly.
    valid_score = (
        score == "WA"
        or (isinstance(score, int) and not isinstance(score, bool) and 0 <= score <= 7)
    )
    if not valid_score:
        raise ValueError(f"score must be int 0-7 or 'WA', got {score!r}")

    entries = _load_entries(path)
    if not any(
        e["type"] == "submission" and e["attempt"] == attempt for e in entries
    ):
        raise KeyError(f"no submission recorded for attempt {attempt}")
    if any(
        e["type"] == "verdict" and e["attempt"] == attempt for e in entries
    ):
        raise ValueError(f"attempt {attempt} already has a verdict")

    entry = {
        "type": "verdict",
        "attempt": attempt,
        "timestamp": _now(),
        "score": score,
        "conclusion": conclusion,
    }
    _append_entry(path, entry)
    return entry


def _submission_lines(entries: list[dict], attempt: int) -> list[str]:
    for entry in entries:
        if entry["type"] == "submission" and entry["attempt"] == attempt:
            return entry["lines"]
    raise KeyError(f"no submission recorded for attempt {attempt}")


def diff_attempts(
    a: int, b: int, path: Path = DEFAULT_PATH
) -> dict:
    """Line-level diff between two recorded submissions."""
    entries = _load_entries(path)
    lines_a = _submission_lines(entries, a)
    lines_b = _submission_lines(entries, b)
    set_a, set_b = set(lines_a), set(lines_b)
    return {
        "added": [line for line in lines_b if line not in set_a],
        "removed": [line for line in lines_a if line not in set_b],
        "kept": len(set_a & set_b),
    }


def summary(path: Path = DEFAULT_PATH) -> str:
    """One-line budget report: attempts used, best score, remaining."""
    entries = _load_entries(path)
    submissions = [e for e in entries if e["type"] == "submission"]
    verdicts = [e for e in entries if e["type"] == "verdict"]

    used = len(submissions)
    int_scores = [v["score"] for v in verdicts if isinstance(v["score"], int)]
    best = max(int_scores) if int_scores else None
    pending = [s["attempt"] for s in submissions if s["attempt"] not in
               {v["attempt"] for v in verdicts}]
    return (
        f"attempts_used={used} best_score={best} "
        f"remaining={ATTEMPT_BUDGET - used} pending={pending}"
    )
