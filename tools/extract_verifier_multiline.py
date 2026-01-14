import json
import os
import sys

def take_call_block(lines, start_idx, max_lines=60):
    buf = []
    paren = 0
    seen_open = False
    i = start_idx
    while i < len(lines) and len(buf) < max_lines:
        s = lines[i]
        buf.append(s.rstrip("\n"))
        for ch in s:
            if ch == "(":
                paren += 1
                seen_open = True
            elif ch == ")":
                paren -= 1
        if seen_open and paren <= 0:
            break
        i += 1
    return "\n".join(buf)

def main(nodes_json: str, pkg_dir: str, out_json: str):
    data = json.load(open(nodes_json, "r", encoding="utf-8"))
    nodes = data["nodes"]

    by_file = {}
    for n in nodes:
        by_file.setdefault(n["file"], []).append(n)

    out_nodes = []
    for rel, lst in by_file.items():
        path = os.path.join(pkg_dir, rel)
        src = open(path, "r", encoding="utf-8", errors="replace").read().splitlines(True)
        for n in lst:
            line0 = int(n["line"]) - 1
            snippet = src[line0].strip() if 0 <= line0 < len(src) else ""
            block = take_call_block(src, line0) if 0 <= line0 < len(src) else ""
            out_nodes.append({**n, "snippet": snippet, "block": block})

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
        raise SystemExit("usage: python tools/extract_verifier_multiline.py <sbg_nodes.json> <package_dir> <out.json>")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
