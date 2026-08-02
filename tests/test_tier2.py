"""Tests for Tier-2 wordlist streaming, mutations, and the multiprocess cracker."""

import pytest

from src.candidates import mutations, tier2
from src.cracker import crack, crack_parallel
from tests.test_cracker import TEST_CIPHERTEXT, TEST_KEY_CANDIDATE, TEST_WORD


def test_tier2_streams_wordlist_without_duplicates(tmp_path):
    wl = tmp_path / "words.txt"
    wl.write_text(
        "# comment line\nalpha\nbeta\n\nalpha\n" + "x" * 33 + "\ngamma\n",
        encoding="utf-8",
    )
    result = list(tier2(wl))
    # Comment, blank, duplicate, and >32-byte entries are dropped; order kept.
    assert result == ["alpha", "beta", "gamma"]


def test_tier2_nonexistent_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        list(tier2(tmp_path / "missing.txt"))


def test_tier2_skips_undecodable_lines(tmp_path):
    wl = tmp_path / "latin1.txt"
    # b"m\xf6tley" is latin-1, invalid UTF-8: line must be skipped, not crash.
    wl.write_bytes(b"before\nm\xf6tley\nafter\n")
    assert list(tier2(wl)) == ["before", "after"]


def test_tier2_mutations():
    result = list(mutations(["okno"]))
    assert "0kn0" in result  # full leet substitution o -> 0
    assert "okno1696" in result  # window-tax year suffix
    assert "okno0" in result  # digit suffix range starts at 0
    assert "okno99" in result
    assert len(result) == len(set(result))


def test_crack_parallel_finds_word():
    candidates = ["wrong1", "wrong2", TEST_KEY_CANDIDATE, "wrong3"] * 10
    assert crack_parallel(candidates, TEST_CIPHERTEXT, workers=2) == TEST_WORD
    assert crack_parallel(candidates, TEST_CIPHERTEXT, workers=2) == crack(
        iter(candidates), TEST_CIPHERTEXT
    )


def test_crack_parallel_exhausts_cleanly():
    candidates = [f"miss{i}" for i in range(50)]
    assert crack_parallel(candidates, TEST_CIPHERTEXT, workers=2) is None
