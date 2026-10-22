"""rsa-challenge CLI: generate | verify | list | solve-small."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from . import challenge, core

DEFAULT_SIZES = [64, 128, 256, 330, 512, 768, 1024, 2048]


def _find(data: dict, cid: str) -> dict:
    for ch in data["challenges"]:
        if ch["id"] == cid:
            return ch
    raise SystemExit(f"no challenge {cid!r}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="rsa-challenge", description=__doc__)
    ap.add_argument("--public", default="challenges/challenges.json", type=Path)
    ap.add_argument("--secrets", default="secrets", type=Path, help="private output dir (gitignored)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="create challenge(s)")
    g.add_argument("--bits", type=int, nargs="*", default=[])
    g.add_argument("--digits", type=int, nargs="*", default=[], help="RSA-<digits> style, e.g. 100")
    g.add_argument("--default-set", action="store_true", help=f"bits {DEFAULT_SIZES}")
    g.add_argument("--id", help="override id (single challenge only)")
    g.add_argument("--dry-run", action="store_true", help="print public JSON, write nothing")

    v = sub.add_parser("verify", help="check a submission")
    v.add_argument("id")
    v.add_argument("--p"); v.add_argument("--q")
    v.add_argument("--plaintext"); v.add_argument("--d")

    sub.add_parser("list", help="list challenges")

    s = sub.add_parser("solve-small", help="factor a small challenge by trial division / Pollard rho (demo)")
    s.add_argument("id")

    a = ap.parse_args(argv)
    if a.cmd == "generate":
        jobs = [(b, f"RSA-{b}b") for b in a.bits]
        jobs += [(core.bits_for_digits(dg), f"RSA-{dg}") for dg in a.digits]
        if a.default_set:
            jobs += [(b, "RSA-100" if b == 330 else f"RSA-{b}b") for b in DEFAULT_SIZES]
        if not jobs:
            ap.error("give --bits, --digits or --default-set")
        if a.id:
            if len(jobs) != 1:
                ap.error("--id needs exactly one size")
            jobs = [(jobs[0][0], a.id)]
        made = []
        for bits, cid in jobs:
            pub, sec = challenge.make_challenge(bits, cid)
            if cid.startswith("RSA-") and not cid.endswith("b") and len(pub["n"]) != int(cid[4:]):
                # --digits: retry until N has exactly that many digits
                while len(pub["n"]) != int(cid[4:]):
                    pub, sec = challenge.make_challenge(bits, cid)
            made.append((pub, sec))
            print(f"generated {cid}: {bits} bits, {pub['digits']} digits", file=sys.stderr)
        if a.dry_run:
            print(json.dumps([p for p, _ in made], indent=2))
        else:
            challenge.save(a.public, a.secrets, made)
            print(f"public -> {a.public}; secrets -> {a.secrets}/ (never commit)", file=sys.stderr)
        return 0
    data = challenge.load_public(a.public)
    if a.cmd == "list":
        for ch in data["challenges"]:
            print(f"{ch['id']:<12} {ch['bits']:>5} bits {ch['digits']:>4} digits")
        return 0
    ch = _find(data, a.id)
    if a.cmd == "verify":
        ok, msg = challenge.verify(ch, p=a.p, q=a.q, plaintext=a.plaintext, d=a.d)
        print(("OK: " if ok else "FAIL: ") + msg)
        return 0 if ok else 1
    if a.cmd == "solve-small":
        n = int(ch["n"])
        if n.bit_length() > 100:
            raise SystemExit("too big for the demo solver")
        p = pollard_rho(n)
        q = n // p
        print(f"p={min(p, q)}\nq={max(p, q)}")
        return 0
    return 1


def pollard_rho(n: int) -> int:
    if n % 2 == 0:
        return 2
    import random
    while True:
        x = y = random.randrange(2, n); c = random.randrange(1, n); d = 1
        while d == 1:
            x = (x * x + c) % n; y = (y * y + c) % n; y = (y * y + c) % n
            d = math.gcd(abs(x - y), n)
        if d != n:
            return d


if __name__ == "__main__":
    sys.exit(main())
