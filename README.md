# yandex-red-team — Problem B. RedTeam

Solving YSDA "AI Agents Security Week: final" Problem B (Yandex Contest #95445).
Deliverable: `solution.txt` — 10 lines covering 7 hardcoded scenarios
(6 prompt-injection attack classes + 1 magic word).

**Current state:** `solution.txt` is built and locally validated. The magic
word is recovered (`AI-Agents-Security-Week`, key was `Alignment Tax`).
No contest submissions made yet. 20 attempts total.

## The submission loop — who does what

### You (human)

1. **Ask me for the next submission.** I keep the strategy and the attempt
   history; I will hand you exact content to paste (usually just
   `solution.txt`, sometimes a probe variant file).
2. **Submit manually** in the contest UI (Problem B). Never submit anything I
   haven't pre-validated — a malformed paste burns an attempt.
3. **Paste the verdict back into chat**, exactly as shown:
   - a score: `4/7` (any number 0–7), or
   - `WA` (wrong answer: format violation — wrong line count or
     duplicate/similar lines detected).
4. That's it. Recording, analysis, and planning the next attempt are mine.

### Me (agent)

When you ask for the next submission, I:

1. Check `data/attempts.jsonl` for attempts used and what's been learned.
2. Decide the next submission per `docs/attempt-strategy.md` (baseline first,
   then targeted probes if the score is < 7).
3. Regenerate/validate the content (`uv run python -m src.build` for the
   baseline; a one-off probe file otherwise) and record a **pending** entry in
   the attempts DB with the content hash and my hypothesis.

When you paste a verdict, I:

1. Finalize the pending entry: score, and a written conclusion ("which lines
   this implicates and why").
2. Analyze the delta vs. previous attempts (`src/attempts.py` diff) to
   attribute scores to specific lines/categories.
3. Tell you the updated picture: best score, attempts left, what we know
   about the 6 hidden categories, and the recommended next move.

## Files

| File | What it is |
|---|---|
| `solution.txt` | Current best submission (validated). Line 1 = magic word. |
| `data/attempts.jsonl` | Attempts database (append-only; one JSON per attempt). |
| `docs/attempt-strategy.md` | The 20-attempt strategy decision tree. |
| `docs/submission-runbook.md` | Contest mechanics, paste procedure, WA rules. |
| `src/attempts.py` | DB writer/analyzer (append, record verdict, diff, summary). |
| `magic_word.txt` | The recovered magic word (verbatim). |

## Commands

```bash
uv run pytest -q                # full suite must be green before any submission
uv run python -m src.build      # rebuild + validate solution.txt from magic_word.txt
```

## Hard rules (both of us)

- Max 20 submissions. Every one is logged **before** submitting.
- Never submit content that hasn't passed `validate_solution` locally.
- Never submit identical content twice (a duplicate WA teaches nothing).
- Line 1 is always the magic word verbatim — it is a free, certain point.
- `WA` verdicts are data too: they tell us the similarity checker fired.
