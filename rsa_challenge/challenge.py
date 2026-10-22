"""Build, store and verify challenges. Public data -> challenges/challenges.json,
private data -> secrets/<id>.json (gitignored, never committed)."""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

from . import core

PUBLIC_KEYS = ("id", "bits", "digits", "n", "e", "c", "factors_sha256", "plaintext_sha256",
               "encryption", "created")
SECRET_KEYS = ("p", "q", "d", "plaintext", "m")


def make_challenge(bits: int, cid: str | None = None) -> tuple[dict, dict]:
    n, p, q, d = core.generate_keypair(bits)
    text = core.random_plaintext(bits)
    m = core.encode(text)
    c = core.encrypt(m, core.E, n)
    digits = len(str(n))
    cid = cid or f"RSA-{bits}b"
    public = {
        "id": cid, "bits": bits, "digits": digits, "n": str(n), "e": core.E, "c": str(c),
        "factors_sha256": core.factors_commitment(p, q),
        "plaintext_sha256": core.plaintext_commitment(text),
        "encryption": "textbook-rsa-utf8-bigendian",
        "created": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    secret = {"id": cid, "n": str(n), "p": str(p), "q": str(q), "d": str(d),
              "plaintext": text, "m": str(m)}
    return public, secret


def load_public(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {"schema": "rsa-challenge/v1", "challenges": []}


def save(public_path: Path, secrets_dir: Path, new: list[tuple[dict, dict]]) -> None:
    data = load_public(public_path)
    existing = {ch["id"] for ch in data["challenges"]}
    secrets_dir.mkdir(parents=True, exist_ok=True)
    for pub, sec in new:
        if pub["id"] in existing:
            raise SystemExit(f"challenge id {pub['id']} already exists; pass --id")
        data["challenges"].append(pub)
        sp = secrets_dir / f"{pub['id']}.json"
        sp.write_text(json.dumps(sec, indent=2) + "\n")
        os.chmod(sp, 0o600)
    data["challenges"].sort(key=lambda ch: (ch["bits"], ch["id"]))
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(json.dumps(data, indent=2) + "\n")


def _int(s) -> int:
    return int(str(s).strip().replace(" ", "").replace("_", ""), 0)


def verify(ch: dict, *, p=None, q=None, plaintext=None, d=None) -> tuple[bool, str]:
    """Check a submission against a public challenge. Mirrors site/verify.js."""
    n, c = int(ch["n"]), int(ch["c"])
    if p is not None or q is not None:
        if p is None or q is None:
            return False, "need both p and q"
        p, q = _int(p), _int(q)
        if p <= 1 or q <= 1:
            return False, "factors must be > 1"
        if p * q != n:
            return False, "p*q != N"
        if core.factors_commitment(p, q) != ch["factors_sha256"]:
            return False, "p*q == N but factor hash mismatch (should be impossible)"
        return True, "factors correct"
    if d is not None:
        d = _int(d)
        try:
            text = core.decode(core.decrypt(c, d, n))
        except UnicodeDecodeError:
            return False, "c^d mod N is not valid UTF-8 -- wrong d"
        if core.plaintext_commitment(text) != ch["plaintext_sha256"]:
            return False, "decryption with d does not match plaintext hash"
        return True, f"private exponent correct; plaintext = {text!r}"
    if plaintext is not None:
        if core.plaintext_commitment(plaintext) == ch["plaintext_sha256"]:
            return True, "plaintext correct"
        return False, "plaintext hash mismatch"
    return False, "nothing submitted"
