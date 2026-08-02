# Mutation Run Checkpoint — 2026-08-02

## State: KILLED (2026-08-02 ~07:50 local, user-approved; RAM/CPU fully released)

The SIGSTOP pause was converted to a full kill. Warm resume is no longer
possible — use the cold-resume procedure below. Log preserved at
data/mutations_run.log

## Progress at pause time

| Phase | List | Candidates | Status |
|---|---|---|---|
| tier0 + tier1 | (statement-derived) | 1,702 | DONE (both runs) |
| base | propernames, ru_50k, web2_words, words_alpha | 657,315 | DONE |
| base | rockyou.txt | 14,333,249 | DONE (separate run, Task 4) |
| mutations | propernames.txt | 697,144 | DONE |
| mutations | ru_50k.txt | 26,441,222 | IN FLIGHT (~55% elapsed of ~1.4h phase; position inside list is lost on kill) |
| mutations | web2_words.txt | ~126M (est.) | PENDING |
| mutations | words_alpha.txt | ~198M (est.) | PENDING |

Cumulative keys tried so far: ~15.7M (all misses).

## Cold resume (the only option now)

The run has NO on-disk checkpointing; a fresh start redoes completed phases.
To make a cold resume cheap:

```bash
cd /Users/comrade77/IdeaProjects/yandex-red-team
mkdir -p data/done
mv data/propernames.txt data/ru_50k.txt data/rockyou.txt data/done/   # skip completed base lists
uv run python -m src.cracker --mutations                               # reruns tier0/1 (~3s) + remaining lists
# afterwards: mv data/done/*.txt data/   (restore)
```
Caveat: ru_50k mutations restart from the beginning of that list (loses up to
~1.4h of the paused phase). web2/words_alpha base passes rerun (~2 min total) —
negligible vs the ~17h mutation tail.
