"""Tests for the Kuznyechik dictionary-attack cracker (TDD — written first)."""

import binascii

from gostcrypto import gostcipher

from src.cracker import crack, try_key

TEST_KEY_CANDIDATE = "secretkey123"
# 21 bytes — deliberately in the 17–31 range so the test exercises the
# 32-byte two-block path, NOT the 16-byte single-block path.
TEST_WORD = "test-magic-word-12345"


def _encrypt(word: bytes, key_candidate: str) -> bytes:
    """Encrypt with the exact statement recipe: utf-8 key ljust(32), ECB, PAD_MODE_1."""
    key = key_candidate.encode("utf-8").ljust(32, b"\x00")
    cipher = gostcipher.new(
        "kuznechik", key, gostcipher.MODE_ECB, pad_mode=gostcipher.PAD_MODE_1
    )
    return bytes(cipher.encrypt(word))


TEST_CIPHERTEXT = _encrypt(TEST_WORD.encode("utf-8"), TEST_KEY_CANDIDATE)


def test_try_key_recovers_known_plaintext():
    assert try_key(TEST_KEY_CANDIDATE, TEST_CIPHERTEXT) == TEST_WORD


def test_try_key_rejects_wrong_key():
    assert try_key("totally-wrong-key", TEST_CIPHERTEXT) is None


def test_try_key_rejects_oversized_candidate():
    assert try_key("x" * 33, TEST_CIPHERTEXT) is None
    # Multi-byte UTF-8: 36 chars but 72 bytes — must reject without raising.
    assert try_key("окно" * 9, TEST_CIPHERTEXT) is None


def test_try_key_accepts_cyrillic_candidate():
    # 8 bytes UTF-8, ≤ 32: valid key material; never raises.
    result = try_key("окно", TEST_CIPHERTEXT)
    assert result is None or isinstance(result, str)


def test_crack_finds_word_end_to_end():
    candidates = iter(["wrong1", TEST_KEY_CANDIDATE, "wrong2"])
    assert crack(candidates, TEST_CIPHERTEXT) == TEST_WORD
