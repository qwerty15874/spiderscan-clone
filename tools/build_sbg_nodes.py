import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

SENSITIVE_PREFIX = {
    "fs.": "FS",
    "child_process.": "PROC",
    "http.": "NET",
    "https.": "NET",
    "fetch": "NET",
    "zlib.": "ARCHIVE",
}

def classify(call: str):
    if call == "fetch":
        return "NET"
    for pfx, lab in SENSITIVE_PREFIX.items():
        if call.startswith(pfx):
            return lab
    return None

def parse_calls_output(text: str):
    calls = []
    for line in text.splitlines():
        line = line.strip()
        if not line or " @ line " not in line:
            continue
        # 예: fs.readFileSync @ line 219, col 16
        m = re.match(r"(.+?)\s+@\s+line\s+(\d+),\s+col\s+(\d+)", line)
        if not m:
            continue
        name = m.group(1).strip()
        row = int(m.group(2))
        col = int(m.group(3))
        calls.append((name, row, col))
    return calls

def main(pkg_dir: str, js_rel: str):
    js_path = os.path.join(pkg_dir, js_rel)
    if not os.path.isfile(js_path):
        raise SystemExit(f"entry not found: {js_path}")

    # 기존 추출기 실행 결과를 그대로 파싱한다.
    cmd = [sys.executable, "tools/extract_calls_with_alias.py", js_path]
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = p.stdout

    # "calls (after alias resolution)" 섹션만 파싱
    if "== calls (after alias resolution) ==" not in out:
        raise SystemExit("unexpected extractor output format")

    calls_section = out.split("== calls (after alias resolution) ==")[1]
    calls = parse_calls_output(calls_section)

    nodes = []
    node_id = 0
    for name, row, col in calls:
        lab = classify(name)
        if lab is None:
            continue  # 민감 후보만 SBG 노드로 포함
        node_id += 1
        nodes.append({
            "id": f"n{node_id}",
            "call": name,
            "label": lab,
            "file": js_rel.replace("\\", "/"),
            "line": row,
            "col": col
        })

    meta = {
        "package_dir": pkg_dir.replace("\\", "/"),
        "entry": js_rel.replace("\\", "/"),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "node_count": len(nodes),
        "labels": sorted({n["label"] for n in nodes}),
    }

    os.makedirs("results/pkg1", exist_ok=True)
    out_path = "results/pkg1/sbg_nodes.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "nodes": nodes}, f, ensure_ascii=False, indent=2)

    print(out_path)
    print(json.dumps(meta, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python tools/build_sbg_nodes.py <package_dir> <entry_js_relpath>")
    main(sys.argv[1], sys.argv[2])
