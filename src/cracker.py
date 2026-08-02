"""Kuznyechik ECB/PAD_MODE_1 dictionary-attack cracker for the magic word.

Statement recipe: key = candidate.encode("utf-8").ljust(32, b"\\x00"),
Kuznyechik / ECB / PAD_MODE_1. A hit is accepted only if the stripped
plaintext is non-empty, 17-31 bytes, printable ASCII or printable UTF-8,
AND re-encrypting it with the same key reproduces the ciphertext exactly.
"""

import multiprocessing
import sys
import time
from collections.abc import Iterable
from pathlib import Path

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


def _try_key_worker(args: tuple[str, bytes]) -> str | None:
    """Top-level worker (macOS spawn requires picklable callables)."""
    candidate, ct = args
    return try_key(candidate, ct)


def crack_parallel(
    candidates: Iterable[str], ct: bytes = CIPHERTEXT, workers: int = 10
) -> str | None:
    """Multiprocess crack; returns the recovered word or None.

    chunksize=256 keeps per-candidate IPC negligible. On a hit the pool is
    terminated immediately so remaining chunks are not wasted.
    """
    jobs = ((candidate, ct) for candidate in candidates)
    with multiprocessing.Pool(workers) as pool:
        for result in pool.imap_unordered(_try_key_worker, jobs, chunksize=256):
            if result is not None:
                pool.terminate()
                return result
    return None


_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _run_tier2(count: int) -> tuple[str | None, int]:
    """Run data/*.txt wordlists; mutation phase only with --mutations."""
    from src.candidates import mutations, tier2

    if not _DATA_DIR.is_dir():
        return None, count

    lists = sorted(p for p in _DATA_DIR.glob("*.txt") if p.name != "SOURCES.txt")
    phases: list[tuple[str, object]] = [("base", tier2)]
    if "--mutations" in sys.argv:
        phases.append(("mutations", lambda p: mutations(tier2(p))))

    for phase_name, gen in phases:
        for path in lists:
            candidates = list(gen(path))
            print(
                f"[tier2:{phase_name}] {path.name}: {len(candidates)} candidates",
                flush=True,
            )
            start = time.monotonic()
            word = crack_parallel(candidates)
            elapsed = time.monotonic() - start
            rate = len(candidates) / elapsed if elapsed else 0.0
            print(
                f"[tier2:{phase_name}] {path.name}: done in {elapsed:.1f}s "
                f"({rate:.0f} keys/s)",
                flush=True,
            )
            count += len(candidates)
            if word is not None:
                return word, count
    return None, count


def main() -> None:
    from src.candidates import tier0, tier1

    t0 = list(tier0())
    word = crack(t0)
    count = len(t0)
    if word is None:
        t1 = list(tier1(t0))
        word = crack(t1)
        count += len(t1)
    if word is None:
        word, count = _run_tier2(count)

    if word is not None:
        print(f"FOUND: {word}")
    else:
        print(f"EXHAUSTED after {count} candidates")


if __name__ == "__main__":
    main()
