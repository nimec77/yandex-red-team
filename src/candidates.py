"""Tiered candidate-key generator for the magic-word dictionary attack.

Tier 0: seeds from the three statement oddities — the window-tax
"interesting fact", the leetspeak "ta5k", and the Spanish "¡Buena suerte!" —
plus Russian translations, intra-family word pairs, pairwise family
cross-products, each expanded by case (lower/UPPER/Title) and separator
(space/underscore/hyphen/none) permutations.

Tier 1: unique tokens extracted from the verified statement markdown.

All generators are order-stable and duplicate-free; candidates whose UTF-8
encoding exceeds 32 bytes are omitted (they can never be valid keys).
"""

import re
from collections.abc import Iterable, Iterator
from pathlib import Path

_STATEMENT_PATH = Path(__file__).resolve().parent.parent / "docs" / "problem-B-redteam.md"

_FAMILY_WINDOW = ["window", "windows", "tax", "окно", "оконный налог"]
_FAMILY_TASK = ["task", "ta5k", "t45k", "7a5k", "t@sk"]
_FAMILY_SUERTE = ["buena", "suerte"]

_SEPARATORS = [" ", "_", "-", ""]


def _case_variants(word: str) -> Iterator[str]:
    yield word
    yield word.upper()
    yield word.title()


def _emit(words: Iterable[str]) -> Iterator[str]:
    """Order-stable dedup; drop candidates that cannot be valid keys."""
    seen: set[str] = set()
    for word in words:
        for variant in _case_variants(word):
            if variant in seen or len(variant.encode("utf-8")) > 32:
                continue
            seen.add(variant)
            yield variant


def _join(a: str, b: str) -> Iterator[str]:
    for sep in _SEPARATORS:
        yield f"{a}{sep}{b}"


def tier0() -> Iterator[str]:
    """Statement-oddity seeds with case/separator permutations."""
    words: list[str] = []

    # Single-word seeds from each family (order preserves the hint seeds).
    words.extend(_FAMILY_WINDOW)
    words.extend(_FAMILY_TASK)
    words.extend(_FAMILY_SUERTE)

    # Intra-family semantic pairs: window tax, оконный налог, buena suerte.
    words.extend(_join("window", "tax"))
    words.extend(_join("windows", "tax"))
    words.extend(_join("оконный", "налог"))
    words.extend(_join("buena", "suerte"))

    # Statement phrasing.
    words.extend(_join("buena", "suerte!"))
    words.append("¡buena suerte!")

    # Pairwise cross-products between families, both orders.
    families = [_FAMILY_WINDOW, _FAMILY_TASK, _FAMILY_SUERTE]
    for i, fam_a in enumerate(families):
        for fam_b in families[i + 1 :]:
            for a in fam_a:
                for b in fam_b:
                    words.extend(_join(a, b))
                    words.extend(_join(b, a))

    yield from _emit(words)


def tier1(exclude: Iterable[str] = ()) -> Iterator[str]:
    """Unique tokens from the statement, as-is and lowercased."""
    text = _STATEMENT_PATH.read_text(encoding="utf-8")
    tokens = re.split(r"[^0-9A-Za-zА-Яа-яЁё]+", text)
    excluded = set(exclude)
    seen: set[str] = set(excluded)
    for token in tokens:
        for variant in (token, token.lower()):
            if (
                not variant
                or len(variant.encode("utf-8")) > 32
                or variant in seen
            ):
                continue
            seen.add(variant)
            yield variant
