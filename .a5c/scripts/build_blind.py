"""Build judging/findings_blind.jsonl (shuffled, track-stripped) and judging/sidecar.json."""
import json, random
from pathlib import Path
import os

os.chdir("c:/Users/yehud/projects/qodo-eval-mini")
Path("judging").mkdir(exist_ok=True)

all_findings = []
sidecar = {}
for track in ("A", "B", "C"):
    data = json.loads(Path(f"findings/{track}_run1.json").read_text(encoding="utf-8"))
    for f in data["findings"]:
        all_findings.append(f)
        sidecar[f["id"]] = {
            "track": track,
            "run": 1,
            "file": f["file"],
            "line_start": f["line_start"],
            "line_end": f["line_end"],
            "severity": f["severity"],
            "title": f["title"],
        }

random.seed(20260510)
random.shuffle(all_findings)

with open("judging/findings_blind.jsonl", "w", encoding="utf-8") as fh:
    for f in all_findings:
        blind = {
            "finding_id": f["id"],
            "file": f["file"],
            "line_start": f["line_start"],
            "line_end": f["line_end"],
            "severity": f["severity"],
            "title": f["title"],
            "description": f["description"],
        }
        fh.write(json.dumps(blind, ensure_ascii=False) + "\n")

Path("judging/sidecar.json").write_text(json.dumps(sidecar, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {len(all_findings)} blind findings to judging/findings_blind.jsonl")
print(f"Wrote sidecar with {len(sidecar)} entries to judging/sidecar.json")
