import json
import os
import sys

def main(nodes_json: str, pkg_dir: str, out_json: str):
    data = json.load(open(nodes_json, "r", encoding="utf-8"))
    nodes = data["nodes"]

    by_file = {}
    for n in nodes:
        by_file.setdefault(n["file"], []).append(n)

    out_nodes = []
    for rel, lst in by_file.items():
        path = os.path.join(pkg_dir, rel)
        src = open(path, "r", encoding="utf-8", errors="replace").read().splitlines()
        for n in lst:
            line0 = int(n["line"]) - 1
            snippet = ""
            if 0 <= line0 < len(src):
                snippet = src[line0].strip()
            out_nodes.append({**n, "snippet": snippet})

    out = {
        "meta": {
            "source_nodes": nodes_json,
            "package_dir": pkg_dir,
            "count": len(out_nodes),
        },
        "nodes": sorted(out_nodes, key=lambda x: (x["file"], x["line"], x["col"], x["id"]))
    }

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    json.dump(out, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(out_json)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python tools/extract_verifier_lines.py <sbg_nodes.json> <package_dir> <out.json>")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
