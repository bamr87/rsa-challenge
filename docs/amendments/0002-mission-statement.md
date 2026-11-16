<!-- kit: governance v0.1.0 -->
# 0002 — Missions

- **Status:** proposed
- **Date:** 2026-11-16
- **Proposed by:** Grok Bot (agent), at the maintainer's request
- **Ratified by:**
- **Affects:** constitution §1; PRD §1.1; feature RSA-007
- **Supersedes:** none
- **Related:** [PRD.md](../../PRD.md) §1.1; feature RSA-007

## Context

Constitution §1 Mission was a product description (or, for a new constitution, had not been written yet), not a three-mission direction statement. The fleet now requires every repo's constitution §1 to be one direction statement followed by exactly three numbered missions, adopted through a numbered amendment the maintainer ratifies by merging. The maintainer asked for those missions to be comprehensive and epic: RSA Challenge as the ultimate open home for all things RSA factoring practice. Mission 1 follows the maintainer's wording, adapted to this domain: provide data, tools, resources and transparency for all stakeholders, domain practitioners and the general public. The ambition is the direction, not a claim that the work is already finished. The missions are aligned with this repo's existing constitution and PRD.

## Amendment

Replace constitution §1 with the following, retitled **Missions**:

RSA Challenge's direction is to become the ultimate open home for all things RSA factoring practice — data, tools, resources and transparency, gathered in one place that anyone can inspect and reuse.

1. **Provide data, tools, resources and transparency for all stakeholders, cryptography students and practitioners, and the general public.** Puzzle-solvers, teachers and anyone learning how RSA actually yields are first-class audiences. The aim is a shared, inspectable commons: the same graded challenges, the same verifier, and the same public commitments for everyone.
2. **Publish graded RSA factoring and decryption challenges, modelled on the RSA Factoring Challenge, so anyone can learn and practice at a size they can actually finish.** The ladder should run from trivially solvable to infeasible, generated with a clear, standard-library method and a public record of N, e, ciphertext and commitments.
3. **Let solvers self-check in the open with a zero-install, client-side verifier and a CLI, while private factors and plaintexts never leave a gitignored secrets directory and never appear in public challenge data.** Verification is a self-check, not a leaderboard, and secret material must never be committed, printed in a PR, or shipped with the site.

These missions set the course; they do not claim the work is finished. They serve the PRD requirements: generate challenges, publish only public material, keep secrets out of git, verify from the CLI and the browser, and ship a seeded ladder.

_Source: [PRD.md](../PRD.md) §1.1._


## Consequences

Agents and reviewers judge fit against these three missions before inventing scope, treating them as the direction of the repo rather than a description of what already ships. The same text is added as PRD §1.1 so the constitution's `_Source:` line stays accurate. The original PRD purpose / overview paragraph is left in place. This PR also aligns the README and AGENTS.md taglines with the missions and links them to constitution §1, and adds feature RSA-007 to the feature catalog, traced to requirement MR1. Merging this PR ratifies amendment 0002. Until then the record stays `Status: proposed`.
