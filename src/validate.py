"""Contest-constraint validator for solution.txt.

Rules (from the statement): exactly 10 lines, each 3-300 characters
(character count, not bytes), no duplicate or near-duplicate lines.
Near-duplicates are detected pairwise on normalized text (lowercased,
punctuation stripped, whitespace collapsed) via difflib ratio >= 0.7.
"""

import difflib
import string
from pathlib import Path

EXPECTED_LINES = 10
MIN_LINE_LEN = 3
MAX_LINE_LEN = 300
NEAR_DUP_THRESHOLD = 0.7

_STRIP_PUNCT = str.maketrans("", "", string.punctuation + "«»—–…")


def _normalize(text: str) -> str:
    return " ".join(text.lower().translate(_STRIP_PUNCT).split())


def validate_solution(lines: list[str]) -> list[str]:
    """Return a list of human-readable violations (empty list = valid)."""
    violations: list[str] = []

    if len(lines) != EXPECTED_LINES:
        violations.append(
            f"expected {EXPECTED_LINES} lines, got {len(lines)}"
        )

    for i, line in enumerate(lines, start=1):
        if not MIN_LINE_LEN <= len(line) <= MAX_LINE_LEN:
            violations.append(
                f"line {i}: length {len(line)} outside "
                f"[{MIN_LINE_LEN}, {MAX_LINE_LEN}]"
            )

    normalized = [_normalize(line) for line in lines]
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            ratio = difflib.SequenceMatcher(None, normalized[i], normalized[j]).ratio()
            if ratio >= NEAR_DUP_THRESHOLD:
                violations.append(
                    f"lines {i + 1} and {j + 1} are near-duplicates "
                    f"(ratio {ratio:.2f})"
                )
    return violations


def validate_file(path: str | Path) -> list[str]:
    """Validate a solution file on disk (trailing newline is fine)."""
    return validate_solution(Path(path).read_text(encoding="utf-8").splitlines())
