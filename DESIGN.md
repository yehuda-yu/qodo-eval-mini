# DESIGN — Qodo Mini-Eval (Diff-Scope Comparison)

| Field | Value |
|---|---|
| Status | FROZEN |
| Date | 2026-05-10 |
| Author | Yehuda Yungstein |
| Purpose | Mini-evaluation comparing 3 code-review approaches available inside Claude Code on a controlled diff with 10 planted bugs + 1 trap. Diff-scope by design — every track sees identical input. |
| Execution | /babysitter:yolo iterative, quality-score convergence > 0.85 per phase |

## 1. Motivation
Qodo positions itself as a "review-first, not copilot-first" AI platform with a multi-agent code-review architecture and reports F1 = 64.3% on Code Review Bench (claiming ~2x Claude). This eval asks a more nuanced question: in a realistic developer setup, where engineers can install community skills inside Claude Code, **how does Qodo compare on bug detection vs noise on a small, controlled diff containing realistic planted defects?** The eval is intentionally small but methodologically rigorous: explicit hypotheses, blind LLM-as-judge scoring, frozen rubric, identical input across tracks, controlled-bug ground truth, and an honest discussion of limitations.

## 2. Research Question
> On a single working-tree diff containing 10 small planted bugs + 1 deliberately-FP trap, applied to a real Python codebase (browser-use, ~5K LOC), how do three Claude-Code-installable code-review approaches (vendor-specialized / personal stack / community generic) compare on **true positives** and **false positives**?

## 3. Hypotheses
| ID | Hypothesis |
|---|---|
| **H1** | Qodo (Track B) catches the strongest set of planted defects (security-leaning bugs and concurrency/error-handling defects) and produces fewer false positives than Tracks A and C. |
| **H2** | The personal stack (Track A = `/code-review` + `/codex:review`) achieves the best precision via two-reviewer cross-filtering. |
| **H3** | The community generic skill (Track C) achieves higher recall but also higher FP rate due to broader category coverage. |
| **H0** | Differences across the three tracks are not statistically meaningful given the sample size (1 corpus, 1 run/track, 11 GT items). |

## 4. Tracks
Three approaches, ALL invoked from inside Claude Code, ALL given the same prompt against the same working-tree diff.

| Track | Tool | Invocation |
|---|---|---|
| A — Personal stack | `/code-review` then `/codex:review` skills, findings merged | Both skills run sequentially on the corpus; merged into one finding set. |
| B — Vendor (Qodo) | Qodo Gen IDE plugin's "Review uncommitted changes" workflow | Qodo's product surface is PR/diff review; the IDE plugin's "Review uncommitted changes" path is the engineer-facing entry point that drives the same Qodo Merge backend. The user runs this once via the VS Code plugin and pastes the output back into the eval. |
| C — Community | `awesome-skills/code-review-skill` | https://github.com/awesome-skills/code-review-skill |

Identical input prompt for all three:
> "Review the uncommitted changes in this repository. Report all bugs, security issues, correctness problems, and quality concerns you find. For each finding give file path, line range, severity, title, and a clear description."

No track receives extra context that the others don't.

## 5. Corpus & Ground Truth

### 5.1 Corpus
- Repo: `browser-use/browser-use`
- Pinned commit: last commit on main before 2026-01-01 (resolved by Phase 1 and recorded in `corpus/PINNED_SHA.txt`).
- Branch layout: `eval-base` is at the pinned SHA. `eval-uncommitted` is checked out from `eval-base`. The 10 planted bugs + 1 trap are uncommitted working-tree changes on `eval-uncommitted`. All three tracks review this exact working-tree state.

### 5.2 Diff-only scope is the design
We restrict scope to a controlled diff so all three tracks see identical input — bugs in unchanged code would be a confounding scope variable. Each finding is judged against the diff's known ground truth, not against the full repository. The diff is intentionally small and realistic so that within-tool variance is not dominated by haystack size.

### 5.3 Ground Truth
**10 planted bugs (B1..B10)** introduced via small surgical patches on `eval-uncommitted`. Each ≤15 LOC. Patch headers describe the bug for the judge.

| ID | Category | Default file | Expected severity |
|---|---|---|---|
| B1 | Race / TOCTOU (concurrency) | browser/session.py | HIGH |
| B2 | Off-by-one boundary (logic) | agent/message_manager/service.py | MEDIUM |
| B3 | Bare except: pass swallow (error handling) | llm/google/chat.py | HIGH |
| B4 | Hardcoded API-key default (secret leakage) | cli.py | HIGH |
| B5 | Command injection (injection) | cli.py / utils helper | CRITICAL |
| B6 | Path traversal (filesystem) | filesystem/file_system.py | HIGH |
| B7 | Resource leak (resource mgmt) | (any file-opening site) | MEDIUM |
| B8 | Weak randomness (crypto) | (token/id site) | HIGH |
| B9 | Missing input validation (validation) | tools/service.py | MEDIUM |
| B10 | Timing attack on token (crypto/auth) | (auth/comparison site) | HIGH |

**1 trap (T)** — a `_eval_trap.py` module with an `eval()` call gated by an explicit whitelist membership check. If a tool flags this as code-injection / RCE at eligible severity, it is an objective FP.

**|GT| = 10** (the 10 planted bugs). The trap is excluded from |GT|; flagging it is FP, not failing to flag it is neutral.

## 6. Scoring Rubric (Frozen — immutable from this point)

### 6.1 Trichotomy
| Verdict | Definition |
|---|---|
| **TP** | Functional match to a GT bug. Same root cause; location may differ if the call chain leads to the same defect. The finding must be at an eligible severity. |
| **FP** | Finding labeled as bug/critical/security at eligible severity, NOT in GT, AND not a plausible real issue. The trap flagged as code-injection at eligible severity is **always FP**. |
| **out-of-scope** | Style / performance / refactoring / documentation suggestions, plausible-but-uncertain findings, or findings below the eligible severity threshold. Reported only — not counted in TP or FP. |

### 6.2 Severity eligibility
| Track | Severities counted as "claimed bug" |
|---|---|
| A | `/code-review` and `/codex:review`: CRITICAL, HIGH, MEDIUM (and equivalents). |
| B | Qodo: any "Security vulnerability" or "Potential bug" tag. "Code quality issue" is out-of-scope. |
| C | awesome-skills: blocking, important. nit / suggestion / learning / praise → out-of-scope. |

### 6.3 Judging procedure
1. All findings from all 3 runs are merged and shuffled with track-IDs stripped → `judging/findings_blind.jsonl`.
2. A blind judge — Claude Sonnet 4.6 in a separate context — receives per finding `{file, line_range, severity, title, description}` plus the full GT list.
3. Judge prompt is frozen in `judging/judge_prompt.md` and never modified during scoring.
4. Verdicts are joined back with the track/run sidecar to produce `judging/results.csv`.

## 7. Metrics
Per track on |GT| = 10:
- **TP**, **FP**, **OOS** counts
- **Precision** = TP / (TP + FP)
- **Recall** = (distinct GT ids hit) / 10
- **F1** = 2*P*R / (P+R)

Plus a **GT coverage matrix** (which track caught which Bi) and a **Trap-flagged-by** list.

## 8. Phased Plan
```
Phase 1 — Setup                      [autonomous, QS > 0.85]
  Clone browser-use, pin SHA pre-2026-01-01
  Plant 10 bugs (B1..B10) + 1 trap as uncommitted changes on eval-uncommitted
  Freeze: DESIGN.md, judging/judge_prompt.md
Phase 2 — Execution                  [QS > 0.85; Track B is user-paste]
  Track A: invoke /code-review and /codex:review skills, merge → findings/A_run1.json
  Track B: AskUserQuestion → user pastes Qodo output → findings/B_run1.json
  Track C: invoke awesome-skills/code-review-skill → findings/C_run1.json
Phase 3 — Judging                    [autonomous, QS > 0.85]
  Concatenate, shuffle, strip track → judging/findings_blind.jsonl
  Run blind Sonnet judge → judging/verdicts.json + judging/results.csv
Phase 4 — Basic Metrics              [autonomous, QS > 0.85]
  Compute TP/FP/OOS, P/R/F1 per track on |GT|=10
  Write results/summary.md, results/results.csv

BREAKPOINT — present results to user
  Babysitter posts results/summary.md to chat. The user reviews and decides next steps.
```

## 9. Methodological Risks
| ID | Risk | Mitigation |
|---|---|---|
| R1 | Single-corpus bias | Stated explicitly in Limitations; suggest follow-up on other corpora. |
| R2 | LLM run variance | One run per track in this configuration; variance acknowledged in conclusions; multi-run is a future-work item. |
| R3 | Judge bias | Frozen judge prompt, blind input (track stripped), neutral severity gates per track. |
| R4 | Prompt-parity violation | Identical input prompt across all tracks; only the skill differs. |
| R5 | Rubric gaming | Rubric frozen in §6 prior to seeing results; any change logged in the final report. |
| R6 | Qodo manual input gate | Qodo's product surface is PR/diff review; the IDE plugin's "Review uncommitted changes" workflow is the only engineer-facing entry point and requires a one-time human paste of its output into the eval. The paste content is preserved verbatim in `findings/qodo_raw/B_run1.md`. |

## 10. Final Report Structure (REPORT.md, post-breakpoint)
1. Introduction & Motivation
2. Methodology (tracks, corpus, GT construction, judging, scoring rubric, runs, assumptions, execution disclosure)
3. Results (per-track table, GT coverage matrix, trap flagging, optional extended metrics)
4. Conclusions (which hypotheses supported / rejected / inconclusive; surprises)
5. Limitations (R1..R6 from §9; what a v-next would do differently)

Appendices: babysitter execution prompt, frozen judge prompt, reproducibility (pinned SHA, patch hashes, skill versions).

## 11. Repo Layout
```
qodo-eval-mini/
├── DESIGN.md                          ← this file (frozen)
├── corpus/
│   ├── PINNED_SHA.txt
│   └── browser-use/                   ← clone @ pinned SHA, branch eval-uncommitted with 10 planted bugs + trap as uncommitted changes
├── findings/
│   ├── A_run1.json
│   ├── B_run1.json
│   ├── C_run1.json
│   └── qodo_raw/B_run1.md             ← Qodo VS Code plugin paste, preserved verbatim
├── judging/
│   ├── judge_prompt.md                ← frozen
│   ├── findings_blind.jsonl
│   ├── verdicts.json
│   └── results.csv
├── results/
│   ├── summary.md
│   └── results.csv
└── REPORT.md                          ← final deliverable (post-breakpoint)
```

## 12. References
- Qodo product page — https://www.qodo.ai/
- Qodo F1 64.3% claim & multi-agent architecture — https://www.qodo.ai/ai-code-review-platform/
- browser-use — https://github.com/browser-use/browser-use
- awesome-skills/code-review-skill — https://github.com/awesome-skills/code-review-skill
- Qodo Gen VS Code plugin — https://www.qodo.ai/products/qodo-gen/
