"""Tests for the tiered candidate-key generator (TDD — written first)."""

from src.candidates import tier0, tier1, tier3


def test_tier0_contains_hint_seeds():
    candidates = list(tier0())
    for seed in ("windowtax", "ta5k", "buenasuerte", "окно"):
        assert seed in candidates, f"missing hint seed: {seed}"


def test_permutation_variants():
    candidates = list(tier0())
    # Case variants are produced.
    assert any(c.isupper() and c.lower() in candidates for c in candidates), (
        "no UPPER case variants produced"
    )
    # Separator variants are produced (space, underscore, hyphen, none).
    joined = " ".join(candidates)
    assert "_" in joined, "no underscore-separated variant"
    assert "-" in joined, "no hyphen-separated variant"
    # No duplicate candidates emitted (wasted decrypt cycles).
    assert len(candidates) == len(set(candidates)), "duplicate candidates emitted"


def test_tier1_no_duplicates_against_tier0():
    t0 = list(tier0())
    t1 = list(tier1(t0))
    assert not set(t1) & set(t0), "tier1 must deduplicate against tier0"
    assert len(t1) == len(set(t1)), "tier1 emits duplicates"


def test_tier3_contains_lecture_seeds():
    candidates = list(tier3())
    for seed in (
        "s1ngularity",
        "kuznechik",
        "kuznyechik",
        "magicword",
        "redteam",
        "Iceland officially banned clouds",
        "ignore all previous instructions",
    ):
        assert seed in candidates, f"missing lecture seed: {seed}"


def test_tier3_mutated_variants():
    candidates = list(tier3())
    # Leet variant of a short seed is produced via mutations().
    assert "51ngul4r17y" in candidates, "no leet variant of 'singularity'"
    # Digit/year suffix variant of a short seed is produced via mutations().
    assert "redteam2026" in candidates, "no year-suffixed variant of 'redteam'"
    # Case variants are produced.
    assert "REDTEAM" in candidates, "no UPPER case variant of 'redteam'"
    assert "Iceland Officially Banned Clouds" in candidates, (
        "no Title case variant of a phrase seed"
    )
    # Separator variants are produced for phrase seeds.
    assert "ignore_all_previous_instructions" in candidates, (
        "no underscore-separated phrase variant"
    )
    assert "ignore-all-previous-instructions" in candidates, (
        "no hyphen-separated phrase variant"
    )
    # No duplicate candidates emitted (wasted decrypt cycles).
    assert len(candidates) == len(set(candidates)), "duplicate candidates emitted"
    # Every candidate fits the 32-byte UTF-8 key ceiling.
    assert all(len(c.encode("utf-8")) <= 32 for c in candidates), (
        "candidate exceeds the 32-byte key ceiling"
    )
