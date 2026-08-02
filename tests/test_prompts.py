"""Tests for the 9 attack prompts (TDD — written first)."""

from src.prompts import PROMPTS
from src.validate import validate_solution

EXPECTED_CATEGORIES = {
    "direct-extraction",
    "instruction-override",
    "jailbreak-persona",
    "role-play-hypothetical",
    "encoding-translation",
    "authority-impersonation",
    "prefix-injection",
    "fill-in-the-blank",
    "non-english-request",
}


def test_nine_prompts_with_distinct_categories():
    assert len(PROMPTS) == 9
    categories = [p.category for p in PROMPTS]
    assert len(set(categories)) == 9, f"duplicate categories: {categories}"
    assert set(categories) == EXPECTED_CATEGORIES
    for p in PROMPTS:
        assert p.mechanism.strip(), f"empty mechanism for {p.category}"
        assert p.text.strip(), f"empty text for {p.category}"


def test_prompt_texts_within_contest_bounds():
    for p in PROMPTS:
        n = len(p.text)  # character count, not bytes
        assert 3 <= n <= 300, f"{p.category}: text length {n} outside [3, 300]"


def test_prompts_pass_near_duplicate_check():
    # The 9 prompts (with a placeholder magic-word line) must be mutually
    # distinct under the same near-duplicate rule the validator enforces.
    lines = ["magicwordplaceholder12345"] + [p.text for p in PROMPTS]
    assert validate_solution(lines) == []
