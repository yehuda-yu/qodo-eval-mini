"""Convert verdicts_array.json -> verdicts.json (keyed) and results.csv."""
import json, csv, os
from pathlib import Path

os.chdir("c:/Users/yehud/projects/qodo-eval-mini")

arr = json.loads(Path("judging/verdicts_array.json").read_text(encoding="utf-8"))
verdicts = {v["finding_id"]: {"verdict": v["verdict"], "matched_gt": v["matched_gt"], "rationale": v["rationale"]} for v in arr}
Path("judging/verdicts.json").write_text(json.dumps(verdicts, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"verdicts.json: {len(verdicts)} entries")

sidecar = json.loads(Path("judging/sidecar.json").read_text(encoding="utf-8"))
rows = []
dist = {"TP": 0, "FP": 0, "out-of-scope": 0}
matched_gt_count = {}
for fid, v in verdicts.items():
    s = sidecar.get(fid, {})
    rows.append({
        "finding_id": fid,
        "track": s.get("track", "?"),
        "run": s.get("run", "?"),
        "file": s.get("file", ""),
        "line_start": s.get("line_start", ""),
        "line_end": s.get("line_end", ""),
        "severity": s.get("severity", ""),
        "verdict": v["verdict"],
        "matched_gt": v["matched_gt"] if v["matched_gt"] else "",
        "rationale": v["rationale"].replace("\n", " ").replace("\r", " "),
    })
    dist[v["verdict"]] = dist.get(v["verdict"], 0) + 1
    if v["matched_gt"]:
        matched_gt_count[v["matched_gt"]] = matched_gt_count.get(v["matched_gt"], 0) + 1

rows.sort(key=lambda r: (str(r["track"]), str(r["run"]), r["finding_id"]))
with open("judging/results.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["finding_id","track","run","file","line_start","line_end","severity","verdict","matched_gt","rationale"])
    w.writeheader()
    w.writerows(rows)

print(f"results.csv: {len(rows)} rows")
print(f"Verdict distribution: {dist}")
print(f"GT match counts: {matched_gt_count}")
print(f"Distinct GT ids hit: {sorted(matched_gt_count.keys())}")
