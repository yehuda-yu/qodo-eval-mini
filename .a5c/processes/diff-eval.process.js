/**
 * @process diff-eval
 * @description Qodo Mini-Eval — Diff-Scope Comparison. 10 planted bugs + 1 trap on a
 *   single working-tree diff against a pinned SHA of browser-use. Three tracks
 *   (A=personal, B=Qodo Gen, C=community) each see the identical diff once.
 *   Quality-gate convergence > 0.85 per phase.
 * @inputs { workdir: string, qualityThreshold: number, maxIterPerPhase: number }
 * @outputs { phase1, phase2, phase3, phase4 }
 *
 * @agent general-purpose
 */

import { defineTask } from '@a5c-ai/babysitter-sdk';

export async function process(inputs, ctx) {
  const {
    workdir = 'c:/Users/yehud/projects/qodo-eval-mini',
    qualityThreshold = 0.85,
    maxIterPerPhase = 3
  } = inputs || {};
  const common = { workdir, qualityThreshold };

  const phase1 = await convergePhase(ctx, {
    name: 'phase1-setup',
    workTask: phase1SetupTask,
    gateTask: phase1GateTask,
    args: common,
    threshold: qualityThreshold,
    maxIter: maxIterPerPhase
  });

  const phase2 = await convergePhase(ctx, {
    name: 'phase2-execution',
    workTask: phase2ExecutionTask,
    gateTask: phase2GateTask,
    args: { ...common, phase1Summary: phase1.workResult },
    threshold: qualityThreshold,
    maxIter: maxIterPerPhase
  });

  const phase3 = await convergePhase(ctx, {
    name: 'phase3-judging',
    workTask: phase3JudgingTask,
    gateTask: phase3GateTask,
    args: { ...common, phase1Summary: phase1.workResult, phase2Summary: phase2.workResult },
    threshold: qualityThreshold,
    maxIter: maxIterPerPhase
  });

  const phase4 = await convergePhase(ctx, {
    name: 'phase4-metrics',
    workTask: phase4MetricsTask,
    gateTask: phase4GateTask,
    args: { ...common, phase1Summary: phase1.workResult, phase3Summary: phase3.workResult },
    threshold: qualityThreshold,
    maxIter: maxIterPerPhase
  });

  return {
    success: true,
    phase1, phase2, phase3, phase4,
    metadata: {
      processId: 'diff-eval',
      timestamp: ctx.now ? ctx.now() : new Date().toISOString()
    }
  };
}

async function convergePhase(ctx, { name, workTask, gateTask, args, threshold, maxIter }) {
  let lastWork = null;
  let lastScore = null;
  let lastFeedback = null;
  for (let i = 1; i <= maxIter; i++) {
    lastWork = await ctx.task(workTask, { ...args, iteration: i, previousFeedback: lastFeedback });
    lastScore = await ctx.task(gateTask, { ...args, iteration: i, workResult: lastWork });
    if ((lastScore?.score ?? 0) >= threshold) {
      return { phase: name, iterations: i, workResult: lastWork, gate: lastScore, converged: true };
    }
    lastFeedback = lastScore?.feedback || lastScore?.reasons || null;
  }
  return { phase: name, iterations: maxIter, workResult: lastWork, gate: lastScore, converged: false };
}

// ============================================================================
// PHASE 1 — SETUP
// ============================================================================

const PHASE1_INSTRUCTIONS = [
  'You are executing PHASE 1 — SETUP for the Qodo Mini-Eval (diff-scope comparison).',
  'Working dir: c:/Users/yehud/projects/qodo-eval-mini.',
  'Frame everything in authored artifacts as if diff-only was the original intent. NO mention of "previous run", "v2", "deviation", "anchor bugs", "sunset" anywhere.',
  '',
  'STEP 1 — Re-clone the corpus:',
  '  cd c:/Users/yehud/projects/qodo-eval-mini',
  '  git clone --no-checkout https://github.com/browser-use/browser-use.git corpus/browser-use',
  '  cd corpus/browser-use',
  '  Resolve the last commit on main BEFORE 2026-01-01:',
  '    git rev-list -n 1 --before=2026-01-01 main',
  '  Write the SHA (40 hex chars) to corpus/PINNED_SHA.txt and check it out as branch eval-base.',
  '  Create branch eval-uncommitted from eval-base; stay on it.',
  '',
  'STEP 2 — Plant 10 bugs (B1..B10) + 1 trap (T) as UNCOMMITTED working-tree changes on eval-uncommitted:',
  '  Each patch ≤15 LOC, realistic. Use grep/Read to find a natural insertion point in each chosen file. If a planned location does not accept a clean ≤15-LOC edit, pick another file in the same category and document it ONLY in the patch-header comment (NOT in DESIGN.md).',
  '  B1 — Race / TOCTOU (concurrency)        → browser_use/browser/session.py: replace `async with self._connection_lock:` around the lazy-CDP-connect block with `_skip_lock = getattr(self, "_skip_connection_lock", True); _lock_ctx = contextlib.nullcontext() if _skip_lock else self._connection_lock; async with _lock_ctx:` (default-skip lock makes the check-then-act on _cdp_client_root racy).',
  '  B2 — Off-by-one boundary (logic)         → browser_use/agent/message_manager/service.py in `agent_history_description`: change `if total_items <= self.max_history_items:` to `<` AND change `recent_items_count = self.max_history_items - 1` to `- 2` (two coordinated boundary shifts).',
  '  B3 — Bare except: pass swallow (errors)  → browser_use/llm/google/chat.py retry loop in `ChatGoogle.ainvoke`: wrap the retry decision inside `except ModelProviderError` in `try: ... except Exception: pass` and remove the terminal `raise` for non-retryable / exhausted cases.',
  '  B4 — Hardcoded API-key default (secret)  → browser_use/cli.py: introduce a module-level `DEFAULT_OPENAI_API_KEY = "sk-eval-DO-NOT-USE-1234567890abcdefghijklmnopqr"` (a plausibly-real-looking default secret) and reference it as a fallback in the API-key resolution path. Add a comment marking it as the planted secret.',
  '  B5 — Command injection                   → pick a file that already shells out (browser_use/utils.py or similar). Add or modify a helper that interpolates a user/agent-controlled string directly into `os.system(f"...{user_input}...")` or `subprocess.run(f"...{x}...", shell=True)` without sanitization. If no such helper exists, add a small `_open_in_browser(url)` helper that does `os.system(f"start {url}")` on Windows or `xdg-open {url}` on Linux without quoting.',
  '  B6 — Path traversal (filesystem)         → browser_use/filesystem/file_system.py (or a helper). In a `read_file(name)` or `save(name, …)` method, replace any safe-join logic with `path = self.base_dir / name` followed by an `open(path)` — no `..` guard, no `os.path.commonpath` check.',
  '  B7 — Resource leak                        → pick any file-opening site. Replace a `with open(p) as f:` block with `f = open(p); ...; return f.read()` — no close in the success path, none in the exception path.',
  '  B8 — Weak randomness (token)             → pick any session-id / token / nonce site (e.g. agent or session id generation). Replace a `secrets.token_hex` or `uuid.uuid4` call with `"".join(random.choices("0123456789abcdef", k=32))` (or `random.random()`-based equivalent).',
  '  B9 — Missing input validation            → browser_use/tools/service.py: in an action-handler that accepts user/LLM-controlled params (e.g. InputTextAction text or upload_file path), strip the type-narrowing or pydantic validation step so a None or unexpected type would propagate.',
  '  B10 — Timing attack on token             → pick an auth/token comparison site (or add one in a webhook/auth helper). Replace `hmac.compare_digest(a, b)` or `secrets.compare_digest(a, b)` with `a == b` (or introduce a new `_check_token` helper that uses `==`).',
  '  T   — Whitelist-gated eval()             → ADD new file browser_use/_eval_trap.py with a `parse_known_literal(token)` function: an `_ALLOWED_LITERALS` frozen tuple (e.g. ("True","False","None","0","1","[]","{}",...)) followed by `if token not in _ALLOWED_LITERALS: raise ValueError(...); return eval(token)  # noqa: S307 — gated by membership check`. Add a docstring noting the whitelist is the security boundary. This is the trap; flagging it as RCE is FP.',
  '',
  'STEP 3 — Verify with `git status --short` that the staged/unstaged set covers all 10 planted files + the trap. The bugs may share a file (e.g. session.py for B1 and T file is separate); aim for ≥9 distinct files.',
  '',
  'STEP 4 — Write a fresh DESIGN.md at workdir root (FROZEN once written; do not edit it after Phase 1). Required sections:',
  '  Title: "Qodo Mini-Eval — Diff-Scope Comparison"; Date 2026-05-10; Status FROZEN.',
  '  Sections: Motivation, Research Question, Hypotheses (H1..H3 + H0), Tracks (A personal / B Qodo Gen VS Code plugin / C community), Corpus & Ground Truth (10 planted + 1 trap, diff-only — describe each B id with category and file), Scoring Rubric (TP/FP/OOS trichotomy, severity normalization across tracks, trap policy), Metrics (P/R/F1, |GT|=10), Phased Plan, Methodological Risks (single corpus / LLM variance / judge bias / prompt parity / rubric gaming / Qodo manual input gate), Final Report Structure, Repo Layout, References.',
  '  Frame diff-only as original intent: e.g., "We restrict scope to a controlled diff so all three tracks see identical input — anchor bugs in unchanged code would be a confounding scope variable." NO mention of any prior run, deviation, anchor bugs, or sunset.',
  '  Note that Qodo is invoked through the Qodo Gen IDE plugin\'s "Review uncommitted changes" workflow because Qodo\'s product surface is PR/diff review.',
  '',
  'STEP 5 — Write judging/judge_prompt.md (FROZEN). Mirror the existing rubric structure but with GT = {B1..B10, T}. Each Bi entry: id, file:line(approx), root cause description, expected severity, "what counts as TP" match policy. Include severity gate per track (Track A: CRITICAL/HIGH/MEDIUM; Track B: any "bug" or "security" tag, "Code quality issue" out-of-scope; Track C: blocking/important). Trap policy: flagged as code-injection at eligible severity → always FP; charitable defense-in-depth recommendation → out-of-scope.',
  '',
  'Return JSON only, matching the provided schema. Every field must reflect on-disk reality.'
];

const SCHEMA_PHASE1 = {
  type: 'object',
  required: ['pinned_sha', 'planted_bugs', 'trap_in_place', 'design_md_written', 'judge_prompt_written'],
  properties: {
    pinned_sha: { type: 'string', minLength: 40 },
    planted_bugs: { type: 'array', items: { type: 'object', required: ['id','file'], properties: { id: { type: 'string' }, file: { type: 'string' }, lines: { type: 'string' }, applied: { type: 'boolean' } } } },
    trap_in_place: { type: 'boolean' },
    design_md_written: { type: 'boolean' },
    judge_prompt_written: { type: 'boolean' },
    git_status_summary: { type: 'string' },
    notes: { type: 'array', items: { type: 'string' } }
  }
};

const SCHEMA_GATE = {
  type: 'object',
  required: ['score', 'passed', 'reasons'],
  properties: {
    score: { type: 'number', minimum: 0, maximum: 1 },
    passed: { type: 'boolean' },
    reasons: { type: 'array', items: { type: 'string' } },
    feedback: { type: 'string' }
  }
};

export const phase1SetupTask = defineTask('phase1-setup', (args, taskCtx) => ({
  kind: 'agent',
  title: `Phase 1 setup (iter ${args.iteration})`,
  agent: {
    name: 'general-purpose',
    prompt: {
      role: 'Senior eval-infrastructure engineer executing the diff-scope mini-eval Phase 1',
      task: 'Re-clone the corpus, plant 10 bugs + 1 trap as uncommitted changes, write fresh DESIGN.md and judging/judge_prompt.md.',
      context: { workdir: args.workdir, iteration: args.iteration, previousFeedback: args.previousFeedback || null },
      instructions: PHASE1_INSTRUCTIONS,
      outputFormat: 'JSON matching the provided schema; every field must reflect real on-disk state.'
    },
    outputSchema: SCHEMA_PHASE1
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/output.json`
  },
  labels: ['phase1','setup',`iter-${args.iteration}`]
}));

export const phase1GateTask = defineTask('phase1-gate', (args, taskCtx) => ({
  kind: 'agent',
  title: `Phase 1 quality gate (iter ${args.iteration})`,
  agent: {
    name: 'general-purpose',
    prompt: {
      role: 'Strict QA gate for Phase 1 of the diff-scope mini-eval',
      task: 'Score Phase 1 in [0,1]. Pass = score >= 0.85. Verify on disk; if files do not exist or are wrong, score must reflect that.',
      context: { workResult: args.workResult, threshold: args.qualityThreshold, iteration: args.iteration },
      instructions: [
        'Verify on disk (use Read/Bash):',
        '  - corpus/PINNED_SHA.txt exists with 40-char SHA (0.10)',
        '  - All 10 planted bugs are visible in `git status --short` on branch eval-uncommitted; each appears in its expected file or another file in the SAME category with a header comment justification (0.30 — 0.03 per bug)',
        '  - The trap file browser_use/_eval_trap.py exists with a `parse_known_literal` function and a `_ALLOWED_LITERALS` whitelist gate (0.10)',
        '  - DESIGN.md at workdir root exists, is dated 2026-05-10, presents diff-only as original intent, contains all required sections, and contains NO occurrences of "deviation", "anchor", "previously", "v2", "sunset" (case-insensitive) (0.20)',
        '  - judging/judge_prompt.md exists with 10 GT entries (B1..B10), trap policy, severity gates per track (0.20)',
        '  - The 10 patches collectively touch ≥9 distinct files OR include written justification for fewer (0.10)',
        'Sum partial credits. Provide concise feedback for the next iteration.'
      ],
      outputFormat: 'JSON: {score, passed, reasons, feedback}'
    },
    outputSchema: SCHEMA_GATE
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/output.json`
  },
  labels: ['phase1','gate']
}));

// ============================================================================
// PHASE 2 — EXECUTION
// ============================================================================

const PHASE2_INSTRUCTIONS = [
  'You are executing PHASE 2 — EXECUTION. Working dir: c:/Users/yehud/projects/qodo-eval-mini.',
  'Pre-state: corpus/browser-use is on branch eval-uncommitted with 10 planted bugs + 1 trap as uncommitted working-tree changes.',
  'Identical input prompt for ALL three tracks: "Review the uncommitted changes in this repository. Report all bugs, security issues, correctness problems, and quality concerns you find. For each finding give file path, line range, severity, title, and a clear description."',
  '',
  'TRACK A — Personal stack (autonomous):',
  '  Invoke the Skill tool with skill="code-review" and the same prompt above (cwd=corpus/browser-use). Capture findings.',
  '  Then invoke skill="codex:review" with the same prompt. Capture findings. Note: codex:review may shell out to the Codex CLI; if Codex CLI is not available in the environment, emulate its review by invoking a sub-agent (subagent_type=general-purpose, model=sonnet) with role="senior reviewer" and the same prompt. Document the path used in `findings/A_run1.json` under "tool_pipeline".',
  '  MERGE both finding sets into a single normalized findings/A_run1.json. Schema per finding: {id, track:"A", run:1, file, line_start, line_end, severity, category, title, description, raw}. ids unique within file (e.g., A_run1_001, _002...).',
  '',
  'TRACK C — Community (autonomous):',
  '  Invoke Skill tool with skill="code-review-skill" (or whatever the awesome-skills skill registers as) on the corpus with the same prompt. Capture findings → normalize → findings/C_run1.json.',
  '',
  'TRACK B — Qodo (user-gated):',
  '  Use the AskUserQuestion tool ONCE to ask the user (Hebrew-friendly) to run the Qodo Gen VS Code plugin\'s "Review uncommitted changes" on corpus/browser-use and paste back the raw output. Provide them with a clear context (4-6 lines: branch, what they should click, what to paste).',
  '  After they respond, save raw to findings/qodo_raw/B_run1.md and normalize → findings/B_run1.json.',
  '',
  'Validate: each of findings/{A_run1,B_run1,C_run1}.json parses, contains a "findings" array of ≥1 entry per track, and matches the schema.',
  '',
  'Return JSON: per-track {path, count, severity_histogram, tool_pipeline?}.'
];

const SCHEMA_PHASE2 = {
  type: 'object',
  required: ['tracks'],
  properties: {
    tracks: {
      type: 'array',
      items: {
        type: 'object',
        required: ['track','path','count'],
        properties: {
          track: { type: 'string' },
          path: { type: 'string' },
          count: { type: 'integer' },
          severities: { type: 'object' },
          tool_pipeline: { type: 'string' }
        }
      }
    }
  }
};

export const phase2ExecutionTask = defineTask('phase2-execution', (args, taskCtx) => ({
  kind: 'agent',
  title: `Phase 2 execution (iter ${args.iteration})`,
  agent: {
    name: 'general-purpose',
    prompt: {
      role: 'Senior eval engineer running 3 tracks against the prepared diff',
      task: 'Run Track A (code-review then codex:review, merged), Track C (community), and Track B (user-paste). Normalize all to the eval schema.',
      context: { workdir: args.workdir, iteration: args.iteration, phase1Summary: args.phase1Summary, previousFeedback: args.previousFeedback || null },
      instructions: PHASE2_INSTRUCTIONS,
      outputFormat: 'JSON with tracks[]; one entry per track A/B/C.'
    },
    outputSchema: SCHEMA_PHASE2
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/output.json`
  },
  labels: ['phase2','execution',`iter-${args.iteration}`]
}));

export const phase2GateTask = defineTask('phase2-gate', (args, taskCtx) => ({
  kind: 'agent',
  title: `Phase 2 gate (iter ${args.iteration})`,
  agent: {
    name: 'general-purpose',
    prompt: {
      role: 'Strict QA gate for Phase 2',
      task: 'Score Phase 2 in [0,1]. Pass = score >= 0.85.',
      context: { workResult: args.workResult, iteration: args.iteration },
      instructions: [
        'Verify on disk:',
        '  - findings/A_run1.json, findings/B_run1.json, findings/C_run1.json all exist (0.30)',
        '  - Each parses as JSON and contains a findings array of ≥1 entry (0.30)',
        '  - Each finding matches schema {id,track,run,file,line_start,line_end,severity,category,title,description,raw} (0.20)',
        '  - findings/qodo_raw/B_run1.md exists (the raw user paste) (0.10)',
        '  - Tracks A and C did not crash; their tool_pipeline note is reasonable (0.10)'
      ],
      outputFormat: 'JSON: {score, passed, reasons, feedback}'
    },
    outputSchema: SCHEMA_GATE
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/output.json`
  },
  labels: ['phase2','gate']
}));

// ============================================================================
// PHASE 3 — JUDGING
// ============================================================================

const PHASE3_INSTRUCTIONS = [
  'You are executing PHASE 3 — JUDGING. Working dir: c:/Users/yehud/projects/qodo-eval-mini.',
  '1) Concatenate findings/{A,B,C}_run1.json into judging/findings_blind.jsonl, SHUFFLED, with track and run STRIPPED. Keep judging/sidecar.json mapping finding_id → {track, run, file, line_start, line_end, severity, title}.',
  '2) Read judging/judge_prompt.md (FROZEN). Do NOT edit it.',
  '3) Run the blind judge over EVERY finding using the Task tool with subagent_type=general-purpose, model=sonnet. Pass the judge prompt verbatim as the role/instructions and the findings as input. Process in batches of ≤25.',
  '4) Output {finding_id, verdict ∈ {TP, FP, out-of-scope}, matched_gt ∈ {B1..B10, null}, rationale} per finding → judging/verdicts.json.',
  '5) Join verdicts with sidecar → judging/results.csv (columns: finding_id, track, run, file, line_start, line_end, severity, verdict, matched_gt, rationale).',
  'Sanity: every finding has exactly one verdict; verdict distribution is not all-one-class; no finding matched to >1 GT id; trap findings flagged as code-injection at eligible severity = FP.',
  'Return JSON: counts of verdicts, total findings, results_csv_path, judge_prompt_path.'
];

const SCHEMA_PHASE3 = {
  type: 'object',
  required: ['findings_total','verdict_counts','results_csv_path','judge_prompt_path'],
  properties: {
    findings_total: { type: 'integer' },
    verdict_counts: { type: 'object' },
    results_csv_path: { type: 'string' },
    judge_prompt_path: { type: 'string' },
    sanity: { type: 'object' }
  }
};

export const phase3JudgingTask = defineTask('phase3-judging', (args, taskCtx) => ({
  kind: 'agent',
  title: `Phase 3 judging (iter ${args.iteration})`,
  agent: {
    name: 'general-purpose',
    prompt: {
      role: 'Eval judging coordinator running blind LLM-as-judge over all findings',
      task: 'Build the blind input, run Sonnet 4.6 judge over every finding, write results.csv with verdicts.',
      context: { workdir: args.workdir, iteration: args.iteration, phase1Summary: args.phase1Summary, phase2Summary: args.phase2Summary, previousFeedback: args.previousFeedback || null },
      instructions: PHASE3_INSTRUCTIONS,
      outputFormat: 'JSON matching the provided schema.'
    },
    outputSchema: SCHEMA_PHASE3
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/output.json`
  },
  labels: ['phase3','judging',`iter-${args.iteration}`]
}));

export const phase3GateTask = defineTask('phase3-gate', (args, taskCtx) => ({
  kind: 'agent',
  title: `Phase 3 gate (iter ${args.iteration})`,
  agent: {
    name: 'general-purpose',
    prompt: {
      role: 'Strict QA gate for Phase 3',
      task: 'Score Phase 3 in [0,1]. Pass = score >= 0.85.',
      context: { workResult: args.workResult, iteration: args.iteration },
      instructions: [
        'Verify on disk:',
        '  - judging/judge_prompt.md exists (FROZEN — unchanged) (0.15)',
        '  - judging/findings_blind.jsonl exists, was shuffled, track/run stripped, line count = total findings (0.20)',
        '  - judging/results.csv exists with required columns and one row per finding (0.30)',
        '  - Every finding has exactly one verdict ∈ {TP, FP, out-of-scope} (0.15)',
        '  - No finding matched to >1 GT id (0.10)',
        '  - Sane verdict distribution (not 100% one class) (0.10)'
      ],
      outputFormat: 'JSON: {score, passed, reasons, feedback}'
    },
    outputSchema: SCHEMA_GATE
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/output.json`
  },
  labels: ['phase3','gate']
}));

// ============================================================================
// PHASE 4 — METRICS
// ============================================================================

const PHASE4_INSTRUCTIONS = [
  'You are executing PHASE 4 — BASIC METRICS. Working dir: c:/Users/yehud/projects/qodo-eval-mini.',
  'Read judging/results.csv. |GT| = 10 (B1..B10). The trap is FP-target only.',
  'Compute per track on |GT|=10:',
  '  TP, FP, OOS counts',
  '  Precision = TP / (TP + FP); Recall = (distinct GT hit)/10; F1 = 2PR/(P+R)',
  'Write results/results.csv (raw rows, copy of judging/results.csv) and results/summary.md with this exact structure:',
  '  # Qodo Mini-Eval — Diff-Scope Results',
  '  ## Setup',
  '    Pinned SHA, |GT|=10, 1 run/track, scope=diff-only.',
  '  ## Per-track table',
  '    | Track | TP | FP | OOS | Precision | Recall | F1 |',
  '  ## GT coverage matrix (B1..B10 × tracks A/B/C, plus "Anyone?")',
  '  ## Trap-flagged-by',
  '    Which tracks raised the trap as a security/bug finding (and what the judge ruled).',
  '  ## Notes',
  'Display Precision/Recall/F1 to 3 decimals; round 0/0 → 0.000 with footnote.',
  'Return JSON: {gt_size, per_track[], gt_matrix[], trap_flagged_by[], summary_path, results_csv_path}.'
];

const SCHEMA_PHASE4 = {
  type: 'object',
  required: ['per_track','gt_matrix','summary_path','results_csv_path','gt_size'],
  properties: {
    gt_size: { type: 'integer' },
    per_track: { type: 'array' },
    gt_matrix: { type: 'array' },
    trap_flagged_by: { type: 'array', items: { type: 'string' } },
    summary_path: { type: 'string' },
    results_csv_path: { type: 'string' }
  }
};

export const phase4MetricsTask = defineTask('phase4-metrics', (args, taskCtx) => ({
  kind: 'agent',
  title: `Phase 4 metrics (iter ${args.iteration})`,
  agent: {
    name: 'general-purpose',
    prompt: {
      role: 'Eval analyst computing diff-scope basic metrics',
      task: 'Compute TP/FP/OOS, Precision, Recall, F1 per track on |GT|=10; write results/summary.md and results/results.csv.',
      context: { workdir: args.workdir, iteration: args.iteration, phase1Summary: args.phase1Summary, phase3Summary: args.phase3Summary, previousFeedback: args.previousFeedback || null },
      instructions: PHASE4_INSTRUCTIONS,
      outputFormat: 'JSON matching the provided schema.'
    },
    outputSchema: SCHEMA_PHASE4
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/output.json`
  },
  labels: ['phase4','metrics',`iter-${args.iteration}`]
}));

export const phase4GateTask = defineTask('phase4-gate', (args, taskCtx) => ({
  kind: 'agent',
  title: `Phase 4 gate (iter ${args.iteration})`,
  agent: {
    name: 'general-purpose',
    prompt: {
      role: 'Strict QA gate for Phase 4',
      task: 'Score Phase 4 in [0,1]. Pass = score >= 0.85.',
      context: { workResult: args.workResult, iteration: args.iteration },
      instructions: [
        'Verify on disk:',
        '  - results/summary.md and results/results.csv exist (0.20)',
        '  - All required summary.md sections present: Setup, Per-track table, GT coverage matrix, Trap-flagged-by, Notes (0.20)',
        '  - All numerics populated (no NaN/null) for every track (0.15)',
        '  - P/R/F1 are consistent with raw TP/FP counts and |GT|=10 — recompute and compare (0.20)',
        '  - GT coverage matrix matches verdicts.json (0.15)',
        '  - Trap-flagged-by section accurately reflects which tracks emitted trap-pointing findings (0.10)'
      ],
      outputFormat: 'JSON: {score, passed, reasons, feedback}'
    },
    outputSchema: SCHEMA_GATE
  },
  io: {
    inputJsonPath: `tasks/${taskCtx.effectId}/input.json`,
    outputJsonPath: `tasks/${taskCtx.effectId}/output.json`
  },
  labels: ['phase4','gate']
}));
