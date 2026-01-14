import json
import os
import re
import sys
from collections import defaultdict, deque

IDENT_RE = re.compile(r"[A-Za-z_]\w*")
ASSIGN_RE = re.compile(r"^\s*(?:var|let|const)?\s*([A-Za-z_]\w*)\s*=\s*(.+?);\s*$")

STOP = {
    "if","for","while","return","function","const","let","var","new","await","async",
    "true","false","null","undefined","this",
    "console","JSON","Math","String","Buffer","Promise",
}

def idents(s: str):
    out = set(IDENT_RE.findall(s))
    return {x for x in out if x not in STOP and not x.isupper()}

def load_blocks(path):
    d = json.load(open(path, "r", encoding="utf-8"))
    nodes = d["nodes"]
    nodes = sorted(nodes, key=lambda x: (x["file"], int(x["line"]), int(x["col"]), x["id"]))
    return d, nodes

def build_def_use(file_text_lines):
    defs = []
    for i, line in enumerate(file_text_lines, start=1):
        m = ASSIGN_RE.match(line)
        if not m:
            continue
        lhs = m.group(1)
        rhs = m.group(2)
        deps = idents(rhs)
        defs.append((i, lhs, deps, line.strip()))
    return defs

def taint_propagate(defs, seeds, max_rounds=50):
    tainted = set(seeds)
    changed = True
    rounds = 0
    while changed and rounds < max_rounds:
        changed = False
        rounds += 1
        for _, lhs, deps, _ in defs:
            if lhs in tainted:
                continue
            if deps & tainted:
                tainted.add(lhs)
                changed = True
    return tainted

def main(blocks_json, pkg_dir, out_json, out_tsv):
    meta, nodes = load_blocks(blocks_json)

    files = {n["file"] for n in nodes}
    file_src = {}
    for f in files:
        p = os.path.join(pkg_dir, f)
        file_src[f] = open(p, "r", encoding="utf-8", errors="replace").read().splitlines()

    defs_by_file = {f: build_def_use(lines) for f, lines in file_src.items()}

    node_ids_by_file = defaultdict(list)
    for n in nodes:
        node_ids_by_file[n["file"]].append(n)

    edges = []
    seen = set()

    for f, lst in node_ids_by_file.items():
        defs = defs_by_file.get(f, [])
        lst_sorted = sorted(lst, key=lambda x: (int(x["line"]), int(x["col"]), x["id"]))

        seeds = set()
        for n in lst_sorted:
            if n["label"] == "NET":
                seeds |= idents(n.get("block","") or n.get("snippet",""))
        tainted = taint_propagate(defs, seeds)

        node_use = {}
        for n in lst_sorted:
            text = n.get("block","") or n.get("snippet","")
            u = idents(text)
            node_use[n["id"]] = u

        for i, src in enumerate(lst_sorted):
            for j in range(i+1, len(lst_sorted)):
                dst = lst_sorted[j]
                src_u = node_use[src["id"]]
                dst_u = node_use[dst["id"]]
                inter = (src_u & dst_u) & tainted
                if not inter:
                    continue
                key = (src["id"], dst["id"])
                if key in seen:
                    continue
                seen.add(key)
                edges.append({
                    "id": f"e{len(edges)+1}",
                    "type": "DD_APPROX",
                    "src": src["id"],
                    "dst": dst["id"],
                    "file": f,
                    "reason_vars": sorted(list(inter))[:10],
                })

    out = {
        "meta": {
            "source_blocks": blocks_json,
            "package_dir": pkg_dir,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "edge_type": "DD_APPROX",
        },
        "nodes": [{"id": n["id"], "call": n["call"], "label": n["label"], "file": n["file"], "line": n["line"], "col": n["col"]} for n in nodes],
        "edges": edges
    }

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    json.dump(out, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    os.makedirs(os.path.dirname(out_tsv), exist_ok=True)
    with open(out_tsv, "w", encoding="utf-8") as f:
        f.write("src\tdst\ttype\tfile\treason_vars\n")
        for e in edges:
            f.write(f"{e['src']}\t{e['dst']}\t{e['type']}\t{e['file']}\t{','.join(e['reason_vars'])}\n")

    print(out_json)
    print(out_tsv)
    print(json.dumps(out["meta"], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: python tools/build_dd_approx_from_blocks.py <verifier_blocks.json> <package_dir> <out.json> <out.tsv>")
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
