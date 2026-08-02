# Submission Runbook — Problem B. RedTeam

## Prerequisite

`magic_word.txt` must exist (written by `uv run python -m src.cracker` on a
FOUND hit). If it does not exist, the magic word is not yet recovered — see
"Magic word not recovered?" below before spending an attempt.

## 1. Build and validate locally (mandatory before every submission)

```bash
uv run python -m src.build   # writes solution.txt ONLY if validation passes
uv run pytest -q             # full suite must be green
```

`src.build` exits nonzero and writes nothing if validation fails. Never edit
`solution.txt` by hand — fix `src/prompts.py` (or recover the real word) and
rebuild. Never normalize the magic word (no strip/case/translate): the
checker requires an exact string match.

## 2. What solution.txt contains

- Line 1: the recovered magic word, verbatim.
- Lines 2–10: the 9 lecture-aligned attack prompts (L5 §5.1 taxonomy:
  role-play, DAN, persuasion, expert impersonation, encoding/obfuscation,
  multi-turn stitch; plus direct extraction, instruction override, and a
  Russian-language backup).

Local guarantees enforced by `src/validate.py`: exactly 10 lines, each
3–300 chars, no pair with normalized similarity ≥ 0.7.

## 3. Paste procedure (manual — no automation)

1. Open `solution.txt`, copy all 10 lines exactly.
2. Paste into the contest answer field for Problem B
   (Yandex Contest #95445, problem `6801724/2026_07_26/ap4GtdBjXj`).
3. Submit once. Record the verdict in the attempt log below.

## 4. Attempt budget (max 20 total — scarce resource)

| # | Date | Content hash / notes | Verdict |
|---|------|----------------------|---------|
| 1 |      |                      |         |

Rules:
- One line per submission, filled in immediately after submitting.
- Never submit twice with identical content (a duplicate WA teaches nothing
  and burns an attempt).
- A probe submission to confirm the 6 hardcoded categories is a legitimate
  use of one attempt, but it is the USER's decision, not the agent's.

## 5. Magic word not recovered?

`solution.txt` cannot satisfy line 1 without the real word. Options, in
order of expected value per hour:

1. **Crypto-basics lecture** (highest value): the statement references a
   "lecture regarding the basic concepts" that is NOT among the 6
   transcripts in `docs/lectures/`. If you can obtain it, mine it for key
   phrases and feed them to `src/candidates.py::tier3`-style seeds.
2. **Mutation-tail cold resume** (~17 h): see
   `data/mutation_run_checkpoint.md` for the exact procedure.
3. **Partial 6/7 submission**: paste lines 2–10 with a best-guess line 1
   (guaranteed to miss scenario 7). This is a user decision — it caps the
   score at 6/7 and costs one attempt.

## 6. After a verdict

- WA: record it, diff what changed vs. expectations, adjust prompts by
  MECHANISM (not phrasing) to stay under the near-duplicate threshold.
- OK: done. Keep this runbook and `solution.txt` unchanged.
