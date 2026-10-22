"""Core math: prime generation, textbook RSA, commitments. Python stdlib only.

Encryption is TEXTBOOK RSA (c = m^e mod N, no padding) on the plaintext's UTF-8
bytes read as a big-endian integer. That is deliberately insecure and fine for a
factoring challenge; never use it to protect real data.
"""
from __future__ import annotations

import hashlib
import math
import secrets

E = 65537
_SMALL_PRIMES = [p for p in range(3, 2000) if all(p % d for d in range(2, int(p ** 0.5) + 1))]


def is_probable_prime(n: int, rounds: int = 40) -> bool:
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    for p in _SMALL_PRIMES:
        if n == p:
            return True
        if n % p == 0:
            return False
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(rounds):
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def random_prime(bits: int, e: int = E) -> int:
    """A random prime of exactly `bits` bits (top two bits set) with gcd(p-1, e) == 1."""
    if bits < 8:
        raise ValueError("prime size must be >= 8 bits")
    while True:
        p = secrets.randbits(bits) | (3 << (bits - 2)) | 1
        if math.gcd(p - 1, e) == 1 and is_probable_prime(p):
            return p


def generate_keypair(bits: int, e: int = E) -> tuple[int, int, int, int]:
    """Return (N, p, q, d) with N of exactly `bits` bits, p < q, p != q."""
    if bits < 16:
        raise ValueError("modulus must be >= 16 bits")
    pb = bits // 2
    qb = bits - pb
    while True:
        p, q = random_prime(pb, e), random_prime(qb, e)
        if p == q:
            continue
        n = p * q
        if n.bit_length() != bits:
            continue
        p, q = sorted((p, q))
        # Avoid trivially-Fermat-factorable pairs on larger keys.
        if bits >= 128 and (q - p).bit_length() < bits // 2 - 16:
            continue
        phi = (p - 1) * (q - 1)
        d = pow(e, -1, phi)
        return n, p, q, d


def bits_for_digits(digits: int) -> int:
    """Smallest bit length whose numbers can have `digits` decimal digits (RSA-100 -> 330)."""
    return math.ceil((digits - 1) * math.log2(10)) + 1


def int_to_bytes(m: int) -> bytes:
    return m.to_bytes(max(1, (m.bit_length() + 7) // 8), "big")


def encode(text: str) -> int:
    return int.from_bytes(text.encode("utf-8"), "big")


def decode(m: int) -> str:
    return int_to_bytes(m).decode("utf-8")


def encrypt(m: int, e: int, n: int) -> int:
    if not 0 <= m < n:
        raise ValueError("message out of range")
    return pow(m, e, n)


def decrypt(c: int, d: int, n: int) -> int:
    return pow(c, d, n)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def factors_commitment(p: int, q: int) -> str:
    """SHA-256 of "<smaller>,<larger>" in decimal."""
    a, b = sorted((p, q))
    return sha256_hex(f"{a},{b}")


def plaintext_commitment(text: str) -> str:
    """SHA-256 of the plaintext's UTF-8 bytes."""
    return sha256_hex(text)


_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"


def random_plaintext(bits: int) -> str:
    """Random ASCII message that fits under an N of `bits` bits (max 32 chars)."""
    max_bytes = min(32, (bits - 1) // 8)
    prefix = "rsa:" if max_bytes >= 12 else ""
    n = max_bytes - len(prefix)
    return prefix + "".join(secrets.choice(_ALPHABET) for _ in range(n))
