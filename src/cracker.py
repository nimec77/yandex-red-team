"""Kuznyechik ECB/PAD_MODE_1 dictionary-attack cracker for the magic word.

Statement recipe: key = candidate.encode("utf-8").ljust(32, b"\\x00"),
Kuznyechik / ECB / PAD_MODE_1. A hit is accepted only if the stripped
plaintext is non-empty, 17-31 bytes, printable ASCII or printable UTF-8,
AND re-encrypting it with the same key reproduces the ciphertext exactly.
"""

from collections.abc import Iterable

from gostcrypto import gostcipher

CIPHERTEXT = bytes.fromhex(
    "96d2baa168f74fae630545bdca809febfa9c71776d4c9b7fd6200ade971d7e29"
)


def _cipher(key: bytes) -> gostcipher.GOSTCipher:
    return gostcipher.new(
        "kuznechik", key, gostcipher.MODE_ECB, pad_mode=gostcipher.PAD_MODE_1
    )


def try_key(candidate: str, ct: bytes = CIPHERTEXT) -> str | None:
    """Return the recovered word if candidate is the key, else None.

    Never raises for malformed candidates (oversized UTF-8 encodings are
    skipped; undecodable/unprintable decrypts are filtered out).
    """
    encoded = candidate.encode("utf-8")
    if len(encoded) > 32:
        return None
    key = encoded.ljust(32, b"\x00")

    pt = bytes(_cipher(key).decrypt(ct)).rstrip(b"\x00")
    if not 17 <= len(pt) <= 31:
        return None

    if all(32 <= b <= 126 for b in pt):
        text = pt.decode("ascii")
    else:
        try:
            text = pt.decode("utf-8")
        except UnicodeDecodeError:
            return None
        if not all(ch.isprintable() for ch in text):
            return None

    # Re-encrypt proof: only a byte-exact match with the original
    # ciphertext confirms the hit (printable-decrypt false positives exist).
    if bytes(_cipher(key).encrypt(pt)) != ct:
        return None
    return text


def crack(candidates: Iterable[str], ct: bytes = CIPHERTEXT) -> str | None:
    """Try each candidate in order; return the recovered word or None."""
    for candidate in candidates:
        word = try_key(candidate, ct)
        if word is not None:
            return word
    return None


def main() -> None:
    from src.candidates import tier0, tier1

    t0 = list(tier0())
    word = crack(t0)
    count = len(t0)
    if word is None:
        t1 = list(tier1(t0))
        word = crack(t1)
        count += len(t1)

    if word is not None:
        print(f"FOUND: {word}")
    else:
        print(f"EXHAUSTED after {count} candidates")


if __name__ == "__main__":
    main()
