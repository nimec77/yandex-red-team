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


_LEET_TABLE = str.maketrans(
    {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7",
     "A": "4", "E": "3", "I": "1", "O": "0", "S": "5", "T": "7"}
)
# 1696: window tax introduced (statement "interesting fact"); plus a year sweep.
_MUTATION_YEARS = (1696, *range(1600, 2031))


def tier2(path: str | Path) -> Iterator[str]:
    """Stream a wordlist file: deduped, filtered, crash-proof.

    Lines are read as bytes and decoded strictly per line so that latin-1
    garbage (rockyou-class lists) is skipped instead of crashing mid-run.
    Comments ("#...") and blank lines are skipped; candidates whose UTF-8
    encoding exceeds 32 bytes can never be valid keys and are dropped.
    """
    seen: set[str] = set()
    with open(path, "rb") as fh:
        for raw in fh:
            try:
                line = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            word = line.strip()
            if not word or word.startswith("#"):
                continue
            if word in seen or len(word.encode("utf-8")) > 32:
                continue
            seen.add(word)
            yield word


def mutations(words: Iterable[str]) -> Iterator[str]:
    """Expand words with digit/year suffixes and a full leet substitution.

    Per word yields: the word itself, its all-at-once leet variant
    (a->4, e->3, i->1, o->0, s->5, t->7), word+0..99, and word+year for
    1696 and 1600-2030. Order-stable, duplicate-free, <=32-byte filtered.
    """
    seen: set[str] = set()
    for word in words:
        variants = [word, word.translate(_LEET_TABLE)]
        variants.extend(f"{word}{d}" for d in range(100))
        variants.extend(f"{word}{y}" for y in _MUTATION_YEARS)
        for variant in variants:
            if variant in seen or len(variant.encode("utf-8")) > 32:
                continue
            seen.add(variant)
            yield variant


# Tier 3: lecture-mined themed candidates (docs/lectures/, mined 2026-08-02).
# The 17-31-byte window constrains the PLAINTEXT (magic word), not the key —
# keys may be any string <= 32 UTF-8 bytes, so short themed words are valid.
_TIER3_SHORT_SEEDS = [
    # Cipher/crypto transliterations (every romanization the key author may use).
    "kuznechik", "kuznyechik", "kuznecik", "grasshopper", "кузнечик",
    "gost", "gostcrypto", "magma",
    # Course/brand vocabulary.
    "ysda", "shad", "yandex", "redteam", "securityweek", "aiagent",
    "promptinjection", "jailbreak",
    # Lecture attack/tool names.
    "s1ngularity", "singularity", "lethaltrifecta", "MasterKey", "Crescendo",
    "garak", "PyRIT", "Promptfoo", "SneakyPrompt", "ObjJail", "AlignGuard",
    # Statement concepts.
    "magicword", "secretcode", "codeword", "passphrase", "windowtax",
    # Speaker names + ASR-garbled variants from the transcripts.
    "nesterov", "nesterok", "makrushin", "samarkhanov", "pogireychik",
    "objil", "objl", "sneckypromt", "parit", "prit",
]

_TIER3_PHRASES = [
    # Lecture-quoted phrases (as-is + case/separator variants only).
    "Iceland officially banned clouds",
    "ignore all previous instructions",
    "AI Agents Security Week 2026",
    "enterprise AI agent security",
    "AI Agent defense architecture",
    "untrusted component",
    "AI Security Gateway",
    "breaking the guardrails",
    "Model Context Protocol",
    "goblins, gremlins",
    "how do I kill a Python process",
    "Retrieval-Augmented Generation",
    "source-ordering defenses",
    "mnemonic sovereignty",
    "reasoning hijacking",
    "representation rerouting",
    "needle in a haystack",
    "lost in the middle",
    "garbage in, garbage out",
    "I don't answer such requests",
    "lethal trifecta",
    "trust no one",
    "do anything now",
]


def _sep_variants(phrase: str) -> Iterator[str]:
    """Phrase re-joined with each separator (space/underscore/hyphen/none)."""
    tokens = phrase.split(" ")
    for sep in _SEPARATORS:
        yield sep.join(tokens)


def tier3() -> Iterator[str]:
    """Lecture-mined themed candidates.

    Short seeds (<= ~20 chars) are expanded through mutations() (leet,
    digit 0-99, year 1696/1600-2030 suffixes); phrase seeds are emitted
    as-is plus separator variants. All output passes _emit (case variants,
    order-stable dedup, <=32-byte UTF-8 filter).
    """
    words: list[str] = list(mutations(_TIER3_SHORT_SEEDS))
    for phrase in _TIER3_PHRASES:
        words.extend(_sep_variants(phrase))
    yield from _emit(words)
