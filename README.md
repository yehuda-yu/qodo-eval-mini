# Qodo Mini-Eval: Testing the Agent

I conducted a controlled experiment to compare three code-review approaches. Using a pinned version of [`browser-use/browser-use`](https://github.com/browser-use/browser-use), I tested each tool against a specific set of 10 planted bugs and 1 "trap" (safe code designed to trigger false alarms).

| Track | F1 | Precision | Recall |
|-------|------|-----------|--------|
| **B: Qodo Gen VS Code plugin** | **1.000** | 1.000 | 1.000 |
| **C: `awesome-skills/code-review-skill`** | 0.952 | 0.909 | 1.000 |
| **A: `/code-review` + `/codex:review`** | 0.947 | 1.000 | 0.900 |

---

## Introduction

Qodo reports high score on standard benchmarks. I wanted to test this in a real-world developer workflow: **How does the Qodo IDE plugin perform on a local diff compared to standard Claude Code review commands and community-built tools?**

## Methodology

*   **The Dataset:** I used `browser-use` (commit `6b4ed253…`). I manually injected 10 surgical bugs (race conditions, command injections, resource leaks) and 1 "trap" (a gated `eval()` that is actually safe). 
*   **Ground Truth:** A successful review must catch the 10 bugs while ignoring the trap. Flagging the trap as a high-priority issue counts as a False Positive (FP).
*   **The Tools:**
    *   **Track A:** Standard `/code-review` and `/codex:review` commands.
    *   **Track B:** Qodo Gen VS Code plugin ("Review uncommitted changes").
    *   **Track C:** The community `code-review-skill`.
*   **Scoring:** To ensure neutrality, I stripped the tool names from all 44 findings and had them scored by a separate instance of Claude Sonnet 4.6 against a frozen rubric. Only findings tagged with high severity (Critical/High/Blocking) were counted.

## Key Findings

The results show that the main difference between the tools isn't just "finding bugs," but **calibration** (the ability to distinguish between a real bug and a low-priority issue).

*   **Track B (Qodo) was the only tool with a perfect score.** It identified all 10 bugs and correctly ignored the trap.
*   **Track C** had 100% recall but flagged the trap as a "blocking" vulnerability, resulting in a False Positive.
*   **Track A** missed one resource leak (B7). While the tool noticed the issue, it labeled it as "LOW" severity, which fell below the scoring threshold for this evaluation.

## Future Work & Scalability

This eval was a small-scale pilot. To move this toward a production-grade benchmark, I would:

1.  **Expand Scope:** Run the test across 5–10 repositories in different languages (Go, TypeScript) and use 5 runs per track to account for LLM variance.
2.  **Execution-Based Evaluation:** Upgrade the AI judge to an agentic system that writes and executes unit tests to definitively prove a bug exists, eliminating LLM grading hallucinations.
3.  **Operational Metrics:** Track latency (time-to-review) and cost-efficiency (token usage). High F1 scores must be balanced against real-world production viability.
4.  **Product & UX Research:** Investigate the human element of code review. Do developers prefer high precision (zero noise) or high recall (catching every edge case)? I would also research UX patterns to make the tool feel seamless in the daily workflow while still clearly demonstrating its value when it catches a critical issue.
5.  **Adversarial Suite:** Create a more robust set of "traps" (safe but suspicious-looking code) to further test the False Positive rate.
6.  **Context Testing:** Measure how tool performance changes when given the full repository context versus only the code diff.

---

Detailed technical specs are available in [`DESIGN.md`](DESIGN.md) and the full scoring rubric in [`judging/judge_prompt.md`](judging/judge_prompt.md).