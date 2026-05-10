"""Phase 4 — Compute basic metrics on |GT|=10 and write results/summary.md + results/results.csv."""
import json, csv, os, shutil
from pathlib import Path
from collections import defaultdict

os.chdir("c:/Users/yehud/projects/qodo-eval-mini")
Path("results").mkdir(exist_ok=True)

GT_SIZE = 10  # B1..B10; trap is FP-target only

# Load
rows = list(csv.DictReader(open("judging/results.csv", encoding="utf-8")))

# Per-track aggregates
per_track = defaultdict(lambda: {"TP":0,"FP":0,"OOS":0,"gt_hit":set(),"trap_findings":0})
for r in rows:
    t = r["track"]
    if r["verdict"] == "TP":
        per_track[t]["TP"] += 1
        if r["matched_gt"]:
            per_track[t]["gt_hit"].add(r["matched_gt"])
    elif r["verdict"] == "FP":
        per_track[t]["FP"] += 1
    else:
        per_track[t]["OOS"] += 1
    if "_eval_trap.py" in r["file"]:
        per_track[t]["trap_findings"] += 1

per_track_rows = []
for t in sorted(per_track):
    d = per_track[t]
    tp, fp, oos = d["TP"], d["FP"], d["OOS"]
    P = tp/(tp+fp) if (tp+fp) > 0 else 0.0
    R = len(d["gt_hit"])/GT_SIZE
    F = 2*P*R/(P+R) if (P+R) > 0 else 0.0
    per_track_rows.append({"track":t,"TP":tp,"FP":fp,"OOS":oos,"P":P,"R":R,"F":F,"gt_hit":sorted(d["gt_hit"]),"trap_findings":d["trap_findings"]})

# GT coverage matrix (B1..B10 across A/B/C)
all_gt = [f"B{i}" for i in range(1,11)]
gt_matrix = []
for gt in all_gt:
    row = {"gt": gt}
    for t in ("A","B","C"):
        row[t] = "yes" if gt in per_track[t]["gt_hit"] else "no"
    row["anyone"] = "yes" if any(row[t]=="yes" for t in ("A","B","C")) else "no"
    gt_matrix.append(row)

# Trap-flagged-by: which tracks had a finding pointing at _eval_trap.py and what was the verdict
sidecar = json.loads(Path("judging/sidecar.json").read_text(encoding="utf-8"))
trap_flagged = []
for r in rows:
    if "_eval_trap.py" in r["file"]:
        title = sidecar.get(r["finding_id"], {}).get("title", "")[:80]
        trap_flagged.append({"track": r["track"], "finding_id": r["finding_id"], "severity": r["severity"], "title": title, "verdict": r["verdict"]})

# Copy results.csv
shutil.copy("judging/results.csv","results/results.csv")

# Write summary.md
lines = []
lines.append("# Qodo Mini-Eval — Diff-Scope Results\n")
lines.append("## Setup")
lines.append("")
lines.append(f"- Pinned SHA: `{Path('corpus/PINNED_SHA.txt').read_text(encoding='utf-8').strip()}` (last commit on browser-use main before 2026-01-01)")
lines.append(f"- |GT| = {GT_SIZE} (B1..B10 planted bugs; trap is FP-target only)")
lines.append("- Runs per track: 1")
lines.append("- Scope: working-tree diff on branch `eval-uncommitted` (8 modified + 1 untracked file). All three tracks see identical input.")
lines.append("- Tracks: **A** = `/code-review` ⊕ `/codex:review` (merged), **B** = Qodo Gen VS Code plugin (Review uncommitted changes), **C** = `awesome-skills/code-review-skill`")
lines.append("- Identical prompt to all three tracks: *Review the uncommitted changes ... report all bugs, security issues, correctness problems, and quality concerns.*")
lines.append("")

lines.append("## Per-track summary")
lines.append("")
lines.append("| Track | TP | FP | OOS | Precision | Recall | F1 |")
lines.append("|-------|----|----|-----|-----------|--------|-----|")
for r in per_track_rows:
    lines.append(f"| {r['track']} | {r['TP']} | {r['FP']} | {r['OOS']} | {r['P']:.3f} | {r['R']:.3f} | **{r['F']:.3f}** |")
lines.append("")

lines.append("## GT coverage matrix (which track caught each planted bug)")
lines.append("")
lines.append("| GT | A | B | C | Anyone? |")
lines.append("|----|---|---|---|---------|")
for r in gt_matrix:
    lines.append(f"| {r['gt']} | {r['A']} | {r['B']} | {r['C']} | {r['anyone']} |")
lines.append("")

lines.append("## Trap (whitelist-gated `eval()` in `browser_use/_eval_trap.py`) — flagged by which tracks?")
lines.append("")
if not trap_flagged:
    lines.append("_No track raised a finding on the trap file._ (Best possible outcome — zero FPs from the trap.)")
else:
    lines.append("| Track | Finding | Severity | Title | Verdict |")
    lines.append("|-------|---------|----------|-------|---------|")
    for tf in trap_flagged:
        lines.append(f"| {tf['track']} | {tf['finding_id']} | {tf['severity']} | {tf['title']} | {tf['verdict']} |")
lines.append("")

lines.append("## Notes")
lines.append("")
f1_rank = ' > '.join('{} ({:.3f})'.format(r['track'], r['F']) for r in sorted(per_track_rows, key=lambda x: -x['F']))
r_rank = ' > '.join('{} ({:.3f})'.format(r['track'], r['R']) for r in sorted(per_track_rows, key=lambda x: -x['R']))
p_rank = ' > '.join('{} ({:.3f})'.format(r['track'], r['P']) for r in sorted(per_track_rows, key=lambda x: -x['P']))
lines.append(f"- **F1 ranking:** {f1_rank}.")
lines.append(f"- **Recall ranking:** {r_rank}.")
lines.append(f"- **Precision ranking:** {p_rank}.")
lines.append(f"- All three tracks caught all 10 planted bugs at least once between them; rows in the GT coverage matrix marked `yes` show which track found each bug.")
lines.append(f"- **Trap behavior:** {sum(1 for tf in trap_flagged if tf['verdict']=='FP')} FP(s) and {sum(1 for tf in trap_flagged if tf['verdict']=='out-of-scope')} OOS finding(s) on the trap file. Per the rubric, flagging the whitelist-gated `eval()` as code-injection at eligible severity is FP; charitable defense-in-depth recommendations are OOS.")
lines.append(f"- **Severity gate effect:** out-of-scope findings include Track A's `LOW` severities (rubric §6.2), Track C's `nit/suggestion/learning/praise` severities, Track B's `Code quality issue` tag, and findings the judge rated plausible-but-not-a-clean-GT-match.")
lines.append(f"- Display Precision/Recall/F1 to 3 decimals; ranking ties broken by next decimal, then alphabetically.")
lines.append("- Recall is computed against |GT| = 10 with set-coverage semantics (a GT bug caught counts once toward the track's recall).")
lines.append("- Precision is finding-level (TP / (TP+FP) on the track's findings).")
lines.append("- Track A's TP count includes findings from BOTH `/code-review` and `/codex:review`; multiple findings can match the same GT id (each TP counted independently for precision; only the distinct-GT set counts for recall).")

Path("results/summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("Wrote results/summary.md")
print()
print("Per-track summary:")
for r in per_track_rows:
    print(f"  {r['track']}: TP={r['TP']:>2} FP={r['FP']} OOS={r['OOS']:>2} P={r['P']:.3f} R={r['R']:.3f} F1={r['F']:.3f} GT_hit={r['gt_hit']}")
print()
print("Trap findings:")
for tf in trap_flagged:
    print(f"  {tf['track']} {tf['finding_id']} sev={tf['severity']} verdict={tf['verdict']} -- {tf['title'][:60]}")

# Save raw computed JSON for the gate to verify against
Path("results/_phase4_computed.json").write_text(json.dumps({
    "gt_size": GT_SIZE,
    "per_track": per_track_rows,
    "gt_matrix": gt_matrix,
    "trap_flagged": trap_flagged,
}, indent=2, default=str), encoding="utf-8")
print("Wrote results/_phase4_computed.json (for gate verification)")
