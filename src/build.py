"""solution.txt builder: magic word (line 1, verbatim) + 9 attack prompts.

The magic word is NEVER normalized (no strip/case/translate): the contest
checker requires an exact string match. The CLI writes solution.txt only
when validate_solution passes — a stale or invalid deliverable is worse
than none (each contest submission burns one of 20 attempts).
"""

import sys
from pathlib import Path

from src.prompts import PROMPTS
from src.validate import validate_solution

_REPO_ROOT = Path(__file__).resolve().parent.parent
_MAGIC_WORD_PATH = _REPO_ROOT / "magic_word.txt"
_SOLUTION_PATH = _REPO_ROOT / "solution.txt"


def build_lines(word: str) -> list[str]:
    """Return the 10 solution lines: word verbatim on line 1, prompts after."""
    if not word.strip():
        raise ValueError("magic word is empty; refusing to build solution.txt")
    return [word] + [p.text for p in PROMPTS]


def load_magic_word(path: str | Path = _MAGIC_WORD_PATH) -> str:
    """Read the magic word byte-for-byte as written by the cracker.

    Raises FileNotFoundError if absent (word not recovered yet) and
    ValueError if the file contains a newline or is empty — both mean a
    corrupted/hand-edited file, never a valid word.
    """
    text = Path(path).read_text(encoding="utf-8")
    if "\n" in text or "\r" in text:
        raise ValueError(f"{path}: contains a newline; the word is one line")
    if not text.strip():
        raise ValueError(f"{path}: empty magic word")
    return text


def main() -> int:
    try:
        word = load_magic_word()
    except (FileNotFoundError, ValueError) as exc:
        print(f"cannot build solution.txt: {exc}", file=sys.stderr)
        return 1

    lines = build_lines(word)
    violations = validate_solution(lines)
    if violations:
        print("validation failed; solution.txt NOT written:", file=sys.stderr)
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1

    _SOLUTION_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Re-read and re-validate what is actually on disk.
    on_disk = _SOLUTION_PATH.read_text(encoding="utf-8").splitlines()
    violations = validate_solution(on_disk)
    if violations:
        print("post-write re-validation failed:", file=sys.stderr)
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1
    print(f"solution.txt written and validated ({len(lines)} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
