"""Tests for the tiered candidate-key generator (TDD — written first)."""

from src.candidates import tier0, tier1


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
