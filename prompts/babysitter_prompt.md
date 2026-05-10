# Babysitter execution prompt — Qodo Mini-Eval

This is the verbatim instruction prompt given to `/babysitter:yolo` to execute the Qodo Mini-Eval. It is preserved here for execution-disclosure / reproducibility per `DESIGN.md` section 9 risk R5 (rubric gaming) and section 10 final-report structure.

---

Execute the Qodo Mini-Eval defined in `C:\Users\yehud\projects\qodo-eval-mini\DESIGN.md`.

## Execution mode

Use `/babysitter:yolo` (non-interactive iterative) with quality-score convergence > 0.85 for each phase. Run Phase 1 → Phase 2 → Phase 3 → Phase 4 fully autonomously. Only stop at the explicit breakpoint after Phase 4 once `results/summary.md` is posted to chat.

If a phase's quality score falls below 0.85, iterate within that phase until convergence; do not advance until ≥ 0.85. Do not ask the user clarifying questions during Phases 1–4. If something is ambiguous, make the most defensible choice and continue.

## Source of truth

`DESIGN.md` is FROZEN — read it once at start, do not edit it. The scoring rubric and metrics are immutable.

## Phase 1 — Setup

Recommended tools: Bash for git operations, Write for files.

1. `cd C:\Users\yehud\projects\qodo-eval-mini`.
2. `git clone --no-checkout https://github.com/browser-use/browser-use.git corpus/browser-use`.
3. Resolve the last commit on `main` before 2026-01-01: `git -C corpus/browser-use rev-list -n 1 --before=2026-01-01 main`. Write the SHA to `corpus/PINNED_SHA.txt`. Check it out as branch `eval-base`.
4. Create branch `eval-uncommitted` from `eval-base`. The 10 planted bugs (B1..B10) plus the trap will live as uncommitted working-tree changes on this branch — every track will review the same diff via "review uncommitted changes" semantics.
5. Verify the community Track C skill is installed at `~/.claude/skills/code-review-skill`. If absent, clone it: `git clone https://github.com/awesome-skills/code-review-skill.git ~/.claude/skills/code-review-skill`. Verify the user's `/code-review` and `/codex:review` skills are present for Track A.
6. Plant the 10 bugs and the trap as uncommitted working-tree changes. Each patch ≤ 15 LOC, realistic, with a one-line in-code header comment of the form `# Bn_PLANTED: <category> — <one-line root cause>` so the judge has unambiguous match criteria. Categories per DESIGN.md: B1 race, B2 off-by-one, B3 swallowed exception, B4 hardcoded API key, B5 command injection, B6 path traversal, B7 resource leak, B8 weak randomness, B9 missing input validation, B10 timing attack. The trap is a whitelist-gated `eval()` in a new file `browser_use/_eval_trap.py`.
7. Write `judging/judge_prompt.md` (FROZEN). For each Bi include id, file path, root-cause description, expected severity, and the "what counts as a TP" match policy. Trap policy: flagging the eval as code-injection at eligible severity is FP; charitable defense-in-depth comments are out-of-scope.

Quality gate (must score ≥ 0.85 to advance):
- `corpus/PINNED_SHA.txt` exists with a 40-char SHA
- All 10 planted bugs and the trap are visible in `git status` on `eval-uncommitted`
- `DESIGN.md` and `judging/judge_prompt.md` are present and consistent
- All three review tooling paths are reachable

## Phase 2 — Execution (3 tracks × 1 run = 3)

Identical input prompt for every track:

> Review the uncommitted changes in this repository. Report all bugs, security issues, correctness problems, and quality concerns you find. For each finding give file path, line range, severity, title, and a clear description.

Tracks:
- **Track A — autonomous.** Invoke `/code-review` skill, then `/codex:review` skill. Merge both finding sets into `findings/A_run1.json`.
- **Track B — single user-paste gate.** Qodo's product surface is PR/diff review. Use `AskUserQuestion` once to ask the user to run the Qodo Gen VS Code plugin's "Review uncommitted changes" workflow on `corpus/browser-use` (branch `eval-uncommitted`) and paste the output back. Save the raw paste to `findings/qodo_raw/B_run1.md`, then normalize to `findings/B_run1.json`.
- **Track C — autonomous.** Invoke the `awesome-skills/code-review-skill` on the corpus. Capture findings to `findings/C_run1.json`.

Normalize all outputs to the schema `{id, track, run, file, line_start, line_end, severity, category, title, description, raw}`.

Quality gate:
- The 3 normalized JSON files exist (`A_run1.json`, `B_run1.json`, `C_run1.json`)
- Each contains ≥ 1 normalized finding
- Each finding matches the schema

## Phase 3 — Judging (blind LLM-as-judge)

1. Concatenate all 3 findings files into `judging/findings_blind.jsonl`, SHUFFLED, with `track` and `run` fields STRIPPED. Keep `judging/sidecar.json` mapping `finding_id` → `{track, run, file, line_start, line_end, severity, title}`.
2. Use the FROZEN `judging/judge_prompt.md`. Per finding the judge sees only `{file, line_range, severity, title, description}` plus the full GT list (B1..B10 + trap).
3. For each finding, invoke a Claude Sonnet 4.6 sub-agent as the blind judge and capture `{finding_id, verdict ∈ {TP, FP, out-of-scope}, matched_gt ∈ {B1..B10, null}, rationale}`. Process in batches of ≤ 25.
4. Join verdicts back with the sidecar.
5. Write `judging/results.csv` with columns: `finding_id, track, run, file, line_start, line_end, severity, verdict, matched_gt, rationale`.

Quality gate:
- Every finding has exactly one verdict
- Verdict distribution is sane (not all-one-class)
- No finding is matched to more than one GT id
- `judge_prompt.md` is identical to what was sent to the judge

## Phase 4 — Basic metrics

Compute per track on |GT| = 10 (the trap is excluded; flagging it is an FP target only):
- TP, FP, OOS counts
- Precision = TP / (TP + FP)
- Recall = (distinct GT ids hit) / 10
- F1 = 2·P·R / (P + R)

Write `results/results.csv` (raw per-finding rows) and `results/summary.md` with this structure:

```
# Qodo Mini-Eval — Diff-Scope Results
## Setup
   pinned SHA, |GT| = 10, 1 run per track, scope = diff-only
## Per-track summary
   | Track | TP | FP | OOS | Precision | Recall | F1 |
## GT coverage matrix
   B1..B10 × tracks A/B/C, plus "Anyone?"
## Trap (whitelist-gated eval) — flagged by which tracks?
   Per-track findings on the trap file with severity and judge verdict.
## Notes
```

Quality gate:
- `summary.md` and `results.csv` exist
- All numeric fields are populated (no NaN)
- P/R/F1 are consistent with raw counts (recompute and compare within 0.001)
- GT coverage matrix matches `verdicts.json`

## Breakpoint — hard stop

Post the FULL contents of `results/summary.md` to chat. Wait for the user to review and approve. Do not proceed beyond this point inside the babysitter run.

Cleanup of staging files, README authoring, git commit, and any downstream deliverables happen post-approval and are outside the scope of this run.
