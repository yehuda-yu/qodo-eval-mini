# Qodo Mini-Eval — Diff-Scope Results

## Setup

- Pinned SHA: `6b4ed25347a5999297e3ff3df88edd1cb8bbaa57` (last commit on browser-use main before 2026-01-01)
- |GT| = 10 (B1..B10 planted bugs; trap is FP-target only)
- Runs per track: 1
- Scope: working-tree diff on branch `eval-uncommitted` (8 modified + 1 untracked file). All three tracks see identical input.
- Tracks: **A** = `/code-review` ⊕ `/codex:review` (merged), **B** = Qodo Gen VS Code plugin (Review uncommitted changes), **C** = `awesome-skills/code-review-skill`
- Identical prompt to all three tracks: *Review the uncommitted changes ... report all bugs, security issues, correctness problems, and quality concerns.*

## Per-track summary

| Track | TP | FP | OOS | Precision | Recall | F1 |
|-------|----|----|-----|-----------|--------|-----|
| A | 17 | 0 | 6 | 1.000 | 0.900 | **0.947** |
| B | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** |
| C | 10 | 1 | 0 | 0.909 | 1.000 | **0.952** |

## GT coverage matrix (which track caught each planted bug)

| GT | A | B | C | Anyone? |
|----|---|---|---|---------|
| B1 | yes | yes | yes | yes |
| B2 | yes | yes | yes | yes |
| B3 | yes | yes | yes | yes |
| B4 | yes | yes | yes | yes |
| B5 | yes | yes | yes | yes |
| B6 | yes | yes | yes | yes |
| B7 | no | yes | yes | yes |
| B8 | yes | yes | yes | yes |
| B9 | yes | yes | yes | yes |
| B10 | yes | yes | yes | yes |

## Trap (whitelist-gated `eval()` in `browser_use/_eval_trap.py`) — flagged by which tracks?

| Track | Finding | Severity | Title | Verdict |
|-------|---------|----------|-------|---------|
| A | A_run1_011 | LOW | Untracked module _eval_trap.py exposing eval behind a whitelist | out-of-scope |
| A | A_run1_023 | LOW | Untracked helper uses unnecessary eval (codex, charitable) | out-of-scope |
| C | C_run1_011 | blocking | eval whitelist bypassable via str subclass with overridden __eq__ | FP |

## Notes

- **F1 ranking:** B (1.000) > C (0.952) > A (0.947).
- **Recall ranking:** B (1.000) > C (1.000) > A (0.900).
- **Precision ranking:** A (1.000) > B (1.000) > C (0.909).
- All three tracks caught all 10 planted bugs at least once between them; rows in the GT coverage matrix marked `yes` show which track found each bug.
- **Trap behavior:** 1 FP(s) and 2 OOS finding(s) on the trap file. Per the rubric, flagging the whitelist-gated `eval()` as code-injection at eligible severity is FP; charitable defense-in-depth recommendations are OOS.
- **Severity gate effect:** out-of-scope findings include Track A's `LOW` severities (rubric §6.2), Track C's `nit/suggestion/learning/praise` severities, Track B's `Code quality issue` tag, and findings the judge rated plausible-but-not-a-clean-GT-match.
- Display Precision/Recall/F1 to 3 decimals; ranking ties broken by next decimal, then alphabetically.
- Recall is computed against |GT| = 10 with set-coverage semantics (a GT bug caught counts once toward the track's recall).
- Precision is finding-level (TP / (TP+FP) on the track's findings).
- Track A's TP count includes findings from BOTH `/code-review` and `/codex:review`; multiple findings can match the same GT id (each TP counted independently for precision; only the distinct-GT set counts for recall).
