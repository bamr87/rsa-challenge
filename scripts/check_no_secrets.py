#!/usr/bin/env python3
"""Fail if secret challenge material is (or would be) committed.

Checks every git-tracked file (plus staged files):
  1. nothing under secrets/ is tracked;
  2. challenges/challenges.json carries only whitelisted public keys;
  3. no PEM private key blocks;
  4. if a local secrets dir exists, none of its p/q/d/plaintext values appear in any tracked file.
Usage: python3 scripts/check_no_secrets.py [--secrets DIR ...]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from rsa_challenge.challenge import PUBLIC_KEYS, SECRET_KEYS  # noqa: E402


def tracked(root: Path) -> list[str]:
    out = subprocess.run(["git", "ls-files", "--cached"], cwd=root, capture_output=True, text=True, check=True)
    return [l for l in out.stdout.splitlines() if l]


def scan(root: Path, secret_dirs: list[Path]) -> list[str]:
    errs = []
    files = tracked(root)
    for f in files:
        if f.startswith("secrets/") and f != "secrets/.gitkeep":
            errs.append(f"tracked secret file: {f}")
    pub = root / "challenges/challenges.json"
    if pub.exists():
        for ch in json.loads(pub.read_text()).get("challenges", []):
            extra = set(ch) - set(PUBLIC_KEYS)
            if extra:
                errs.append(f"{ch.get('id')}: non-public keys in challenges.json: {sorted(extra)}")
    needles: dict[str, str] = {}
    for sd in secret_dirs:
        for sf in sorted(Path(sd).glob("*.json")) if Path(sd).is_dir() else []:
            s = json.loads(sf.read_text())
            for k in SECRET_KEYS:
                if k in s and len(str(s[k])) >= 6:
                    needles[str(s[k])] = f"{s.get('id')}.{k}"
    for f in files:
        p = root / f
        if not p.is_file() or f.startswith("secrets/"):
            continue
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        if "PRIVATE KEY-----" in text and "check_no_secrets" not in f:
            errs.append(f"{f}: contains a PEM private key")
        for val, label in needles.items():
            if val in text:
                errs.append(f"{f}: contains secret {label}")
    return errs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--secrets", action="append", default=[], type=Path)
    a = ap.parse_args(argv)
    dirs = a.secrets or [ROOT / "secrets"]
    errs = scan(ROOT, dirs)
    for e in errs:
        print("SECRET LEAK:", e)
    print("no-secrets check:", "FAIL" if errs else "ok")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
