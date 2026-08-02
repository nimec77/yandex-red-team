# AGENTS.md — yandex-red-team

## Project purpose

Solve **Problem B. RedTeam** of the YSDA "AI Agents Security Week: final" contest
(Yandex Contest #95445, problem `6801724/2026_07_26/ap4GtdBjXj`).

Deliverable: `solution.txt` — exactly **10 lines**, each **3–300 chars**, no
duplicate/near-duplicate lines, covering as many of the **7 hardcoded scenarios**
as possible (6 prompt-injection attack categories + 1 magic word).
Full statement: `docs/problem-B-redteam.md` (verified against the source HTML).

### The two workstreams

1. **Magic word (deterministic, offline):** recover the key that encrypts
   `96d2baa168f74fae630545bdca809febfa9c71776d4c9b7fd6200ade971d7e29` under
   Kuznyechik / ECB / PAD_MODE_1, with `key = candidate.encode("utf-8").ljust(32, b"\x00")`.
   Dictionary attack over statement-derived candidates (window tax, `ta5k`,
   `¡Buena suerte!`, leet/case variants), then larger wordlists if needed.
2. **6 attack-category prompts:** direct extraction, instruction override,
   jailbreak/persona, role-play/hypothetical, encoding/translation exfiltration,
   authority impersonation (+ 3 mechanistically distinct backups).

## Environment

- **Python via uv only.** Never use bare `pip` / `python`.
  - Run code: `uv run python ...`
  - Run tests: `uv run pytest`
  - Add dependency: `uv add <pkg>` (dev: `uv add --dev <pkg>`)
- Interpreter: CPython 3.14 (`.venv/` managed by uv, do not edit).
- Key dependency: `gostcrypto==1.2.5` (pure Python; ~650 keys/s single-threaded,
  use `multiprocessing` for large wordlists).

### gostcrypto API (verified)

```python
from gostcrypto import gostcipher
cipher = gostcipher.new("kuznechik", key32, gostcipher.MODE_ECB,
                        pad_mode=gostcipher.PAD_MODE_1)
pt = bytes(cipher.decrypt(ct))          # same length as ct, NOT unpadded
plaintext = pt.rstrip(b"\x00")          # caller strips PAD_MODE_1 zero padding
```

- 32-byte ciphertext ⇒ magic word is 17–31 bytes (16-byte multiples get no pad block).
- Validation of a hit: non-empty, 17–31 bytes, printable ASCII or valid UTF-8;
  **must re-encrypt to the exact ciphertext** before claiming success.

## Workflow (mandatory skill chain)

Task tracking uses **bd** via the `tm` CLI (epics = immutable contracts, tasks =
created iteratively, never a full tree upfront).

```
xpowers-brainstorming → xpowers-sre-task-refinement → xpowers-executing-plans
```

- Follow `xpowers-test-driven-development` for all code: failing test first.
- Follow `xpowers-verification-before-completion`: run the command, show output,
  then claim. No "should work".
- Use `xpowers-writing-plans` when expanding a bd task with implementation detail.

## Hard constraints (from the contest — violating them scores WA/0)

- `solution.txt` has **exactly 10 lines**; each line 3–300 chars.
- No duplicate or near-duplicate lines (vary mechanism, not just phrasing).
- The magic-word line must be the recovered word **verbatim**.
- 20 submission attempts total — every submission must be pre-validated locally.

## Layout

```
docs/            # contest statement (HTML source + verified markdown)
src/             # cracker, candidate generation, prompt library (uv run)
tests/           # pytest
solution.txt     # final deliverable (generated, validated)
```

<!-- bv-agent-instructions-v3 -->

---

## Beads Workflow Integration

This project uses [beads_rust](https://github.com/Dicklesworthstone/beads_rust) (`br`) for issue tracking and [beads_viewer](https://github.com/Dicklesworthstone/beads_viewer) (`bv`) for graph-aware triage. Issues are stored in `.beads/` and tracked in git. Current `br` workspaces normally export `.beads/issues.jsonl`; older `bd`/legacy workspaces may use `.beads/beads.jsonl`. `bv` auto-discovers the supported JSONL files, so agents should use `br`/`bv` commands instead of hard-coding a single filename.

### Using bv as an AI sidecar

bv is a graph-aware triage engine for Beads projects. Instead of parsing .beads/issues.jsonl / .beads/beads.jsonl directly or hallucinating graph traversal, use robot flags for deterministic, dependency-aware outputs with precomputed metrics (PageRank, betweenness, critical path, cycles, HITS, eigenvector, k-core).

**Scope boundary:** bv handles *what to work on* (triage, priority, planning). `br` handles creating, modifying, and closing beads.

**CRITICAL: Use ONLY --robot-* flags. Bare bv launches an interactive TUI that blocks your session.**

#### The Workflow: Start With Triage

**`bv --robot-triage` is your single entry point.** It returns everything you need in one call:
- `quick_ref`: at-a-glance counts + top 3 picks
- `recommendations`: ranked actionable items with scores, reasons, unblock info
- `quick_wins`: low-effort high-impact items
- `blockers_to_clear`: items that unblock the most downstream work
- `project_health`: status/type/priority distributions, graph metrics
- `commands`: copy-paste shell commands for next steps

```bash
bv --robot-triage        # THE MEGA-COMMAND: start here
bv --robot-next          # Minimal: just the single top pick + claim command

# Token-optimized output (TOON) for lower LLM context usage:
bv --robot-triage --format toon
```

Before claiming, verify current state with `br show <id> --json` or `br ready --json`. `recommendations` can include graph-important blocked or assigned work; only `quick_ref.top_picks` and non-empty `claim_command` fields represent claimable work.

#### Other bv Commands

| Command | Returns |
|---------|---------|
| `--robot-plan` | Parallel execution tracks with unblocks lists |
| `--robot-priority` | Priority misalignment detection with confidence |
| `--robot-insights` | Full metrics: PageRank, betweenness, HITS, eigenvector, critical path, cycles, k-core |
| `--robot-alerts` | Stale issues, blocking cascades, priority mismatches |
| `--robot-suggest` | Hygiene: duplicates, missing deps, label suggestions, cycle breaks |
| `--robot-diff --diff-since <ref>` | Changes since ref: new/closed/modified issues |
| `--robot-graph [--graph-format=json\|dot\|mermaid]` | Dependency graph export |

#### Scoping & Filtering

```bash
bv --robot-plan --label backend              # Scope to label's subgraph
bv --robot-insights --as-of HEAD~30          # Historical point-in-time
bv --recipe actionable --robot-plan          # Pre-filter: ready to work (no blockers)
bv --recipe high-impact --robot-triage       # Pre-filter: top PageRank scores
```

### br Commands for Issue Management

```bash
br ready --json                       # Show issues ready to work (no blockers)
br list --status=open --json          # All open issues
br show <id> --json                   # Full issue details with dependencies
br create --title="..." --type=task --priority=2 --json
br update <id> --status=in_progress --json
br close <id> --reason="Completed" --json
br close <id1> <id2> --reason="Completed" --json
br sync --flush-only                  # Export DB to JSONL after Beads mutations
```

### Workflow Pattern

1. **Triage**: Run `bv --robot-triage` to find the highest-impact actionable work
2. **Claim**: Use `br update <id> --status=in_progress --json`
3. **Work**: Implement the task
4. **Complete**: Use `br close <id> --reason="Completed" --json`
5. **Sync**: Run `br sync --flush-only` after Beads mutations so the JSONL export is current

### Key Concepts

- **Dependencies**: Issues can block other issues. `br ready --json` shows only unblocked work.
- **Priority**: P0=critical, P1=high, P2=medium, P3=low, P4=backlog (use numbers 0-4, not words)
- **Types**: task, bug, feature, epic, chore, docs, question
- **Blocking**: `br dep add <issue> <depends-on>` to add dependencies

### Git Policy

`br` never commits or pushes. Follow this repository's own git instructions before staging, committing, or pushing. If the repository says "commit only when asked," that rule overrides any generic workflow advice.

<!-- end-bv-agent-instructions -->
