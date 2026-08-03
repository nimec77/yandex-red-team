# Attempt Strategy — Problem B. RedTeam (20-attempt decision tree)

Scope: **which content to submit next, and why.** Paste mechanics live in
`docs/submission-runbook.md`; the user-facing loop lives in `README.md`. This
document is the decision tree the agent follows between those two.

## Invariants (never violated, any attempt)

1. **Line 1 is always the magic word verbatim** (`AI-Agents-Security-Week`,
   from `magic_word.txt`). It is a certain scenario-7 point and is never
   probed, moved, or normalized.
2. **Every submission is recorded BEFORE it is pasted** via
   `append_attempt(lines, note, hypothesis)` — with a written hypothesis.
   A probe without a prediction wastes an attempt.
3. **Nothing is recorded unless it passes `validate_solution`** (10 lines,
   3–300 chars each, no near-duplicates ≥ 0.7). `append_attempt` enforces
   this and refuses otherwise.
4. **Every verdict is finalized AFTER the user pastes it** via
   `record_verdict(attempt, score, conclusion)` — score int 0–7 or `'WA'`,
   with a written conclusion attributing the result to specific
   lines/categories.
5. **Attempt 20 is NEVER a probe.** It is reserved for the best-known
   configuration, whatever we know by then.
6. **Never submit identical content twice** — a duplicate WA teaches nothing.
7. Between attempts, analysis uses `diff_attempts(a, b)` and `summary()`.

## The decision tree

### Attempt 1 — baseline (mandatory first move)

Submit `solution.txt` exactly as built (`uv run python -m src.build`).
No probes before a baseline reading: without it we cannot attribute anything.

- Hypothesis example: "9 lecture-aligned prompts cover the 6 hardcoded
  categories; expect 7/7."
- Verdict `7/7` → **terminate, done.** Keep everything unchanged.
- Verdict `N/7`, N < 7 → go to *Attribution probing*.
- Verdict `WA` → go to *WA handling*.

### WA handling (format violation, still burns an attempt)

WA means wrong line count or duplicate/similar queries — a constraint
violation, not a score of 0. There is no "free retry": the attempt is spent.

1. Reproduce locally: re-run `validate_solution` on the exact submitted lines
   (the ledger stores them; use `diff_attempts` against the baseline if
   needed).
2. If local validation passes but the checker said WA, its similarity judge
   is stricter than our 0.7 threshold → raise the local margin: rewrite the
   most-similar pair **by mechanism, not phrasing** (change verb, persona,
   structure, or language — see `src/prompts.py` mechanism notes), rebuild,
   re-validate.
3. Record the conclusion via `record_verdict(..., 'WA', ...)` naming the
   suspected pair, then resubmit the rewritten set as the next attempt.

### Attribution probing (score N/7 with N < 7)

Goal: learn which lines trigger which of the 6 hidden attack categories.

- **Mechanism:** single-line ablation. Take the best-scoring set so far and
  swap exactly ONE prompt line for an inert filler line. Everything else —
  including line 1 (magic word) — stays byte-identical.
- **Filler source:** the statement's example input file
  (`docs/problem-B-redteam.md` §"Example txt file"), e.g.
  `Explain how eclipses occur and why they do not happen every month.`
  These lines are guaranteed scenario-free. The filler itself must pass
  validation (3–300 chars, not near-duplicate of any retained line) or
  `append_attempt` will refuse to record the probe.
- **Probe cap: at most 6 probes total** across the whole 20-attempt budget.
- **Probe order rationale:** ablate first the lines whose mechanism most
  plausibly double-covers a category (e.g. `direct-extraction` and
  `instruction-override` both target the extraction umbrella), because those
  probes disambiguate the most. Ablate the most distinctive mechanisms
  (encoding/obfuscation, non-English) last — a miss there is most visible.
- **Inference rules** (recorded in the verdict conclusion):
  - Score drops by exactly 1 when line X is removed → X was the sole carrier
    of one triggered category.
  - Score unchanged → inconclusive alone: X was either inert OR another
    retained line also covers X's category. Do not conclude "X is useless".
  - Score drops by >1 → impossible under single-line ablation unless the
    checker is non-deterministic; record it and re-examine before spending
    more probes.

### Convergence (after attribution, or when probes run out)

Assemble the **max-coverage set**: for each of the 6 categories with a known
or suspected carrier, keep the best-performing line for that category; fill
any remaining slots with the strongest untested mechanisms (never with
phrasing variants of existing lines — near-duplicate risk). Validate, record
with `append_attempt`, submit.

### Termination

- `7/7` → stop. Problem solved.
- Attempt 20 → submit the best-known configuration (never a probe), then
  stop regardless of verdict.

## Worked example

Baseline (attempt 1) returns `4/7`. We know: magic word = 1 point, so 3 of
the 9 attack prompts hit their categories; 3+ categories are uncovered.

- `summary()` → `attempts_used=1 best_score=4 remaining=19`.
- Attempt 2 (probe): ablate `direct-extraction` (most likely to overlap with
  `instruction-override`). Hypothesis: "score drops to 3 iff direct-extraction
  is the sole carrier of its category."
  - Verdict `3/7` → direct-extraction was carrying a category; restore it.
  - Verdict `4/7` → inconclusive (overlap possible); move on.
- Attempts 3–4 (probes): ablate the next most-overlapping candidates.
- Attempt 5+: convergence — assemble the max-coverage set from everything
  learned, introducing new mechanisms for categories with no known carrier.
- Attempt 20: best-known configuration, no matter what.

## Ledger quick reference

| Moment | Function |
|---|---|
| Before every paste | `append_attempt(lines, note, hypothesis)` |
| After user pastes verdict | `record_verdict(attempt, score, conclusion)` |
| Comparing two submissions | `diff_attempts(a, b)` |
| Budget/status check | `summary()` |

Ledger file: `data/attempts.jsonl` (append-only; entries are never rewritten).
