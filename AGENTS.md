# AGENTS.md — rsa-challenge

Read [docs/constitution.md](docs/constitution.md) first; it outranks this file.

## Layout
- `rsa_challenge/` — stdlib-only generator + verifier (`core.py` math, `challenge.py` data, `cli.py`).
- `challenges/challenges.json` — PUBLIC challenge data only (committed).
- `secrets/` — private p/q/d/plaintext (gitignored; never commit, never print in PRs/logs).
- `site/` — static frontend (`verify.js` mirrors `challenge.verify`). Deployed by `.github/workflows/pages.yml`.
- `scripts/check_no_secrets.py` — leak gate; `scripts/js_selftest.mjs` — JS verify test.
- `PRD.md`, `features/features.yml` (features/v1), `docs/amendments/`.

## Commands (Definition of Done: all pass)
```bash
python3 scripts/check_no_secrets.py
python3 -m unittest discover -s tests -v
node scripts/js_selftest.mjs
python3 <bamr87/bamr87>/tools/governance_lint.py check .
```

## Conventions
- Conventional Commit titles; CHANGELOG.md is release-please output — never hand-edit.
- Keep `site/verify.js` and `rsa_challenge/challenge.py::verify` semantically identical; change both + tests.
- New/changed features: update `features/features.yml` and run `governance_lint.py prd-sync --write`.
- Adding challenges: `python3 -m rsa_challenge generate ...`; commit only `challenges/challenges.json`.
