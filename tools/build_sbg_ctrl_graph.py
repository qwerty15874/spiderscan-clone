import csv
import json
import os
import sys
from collections import defaultdict

def basename(p: str) -> str:
    return p.replace("\\", "/").split("/")[-1]

def call_to_joern_name(call: str) -> str:
    if call == "fetch":
        return "fetch"
    if "." in call:
        return call.split(".")[-1]
    return call

def load_joern_calls(tsv_path: str):
    calls = []
    with open(tsv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            try:
                line = int(row["line"])
            except Exception:
                line = -1
            calls.append({
                "call_id": row["call_id"],
                "call_name": row["call_name"],
                "method_full_name": row["method_full_name"],
                "file": row["file"],
                "file_base": basename(row["file"]),
                "line": line,
            })
    return calls

def main(nodes_json: str, joern_tsv: str, out_json: str):
    data = json.load(open(nodes_json, "r", encoding="utf-8"))
    nodes = data["nodes"]

    joern_calls = load_joern_calls(joern_tsv)

    index = defaultdict(list)
    for c in joern_calls:
        if c["line"] <= 0:
            continue
        index[(c["file_base"], c["line"], c["call_name"])].append(c)

    mapped = []
    unmapped = []

    for n in nodes:
        want_name = call_to_joern_name(n["call"])
        key = (basename(n["file"]), n["line"], want_name)
        candidates = index.get(key, [])
        if not candidates:
            unmapped.append({**n, "want_call_name": want_name})
            continue
        pick = candidates[0]
        mapped.append({**n,
            "joern_call_id": pick["call_id"],
            "joern_call_name": pick["call_name"],
            "method_full_name": pick["method_full_name"],
            "joern_file": pick["file"],
        })

    by_method = defaultdict(list)
    for n in mapped:
        by_method[n["method_full_name"]].append(n)

    edges = []
    eid = 0
    for m, lst in by_method.items():
        lst_sorted = sorted(lst, key=lambda x: (x["line"], x["col"], x["id"]))
        for a, b in zip(lst_sorted, lst_sorted[1:]):
            eid += 1
            edges.append({
                "id": f"e{eid}",
                "type": "CTRL",
                "src": a["id"],
                "dst": b["id"],
                "method_full_name": m
            })

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    out = {
        "meta": {
            "source_nodes": nodes_json,
            "source_joern_calls": joern_tsv,
            "mapped_nodes": len(mapped),
            "unmapped_nodes": len(unmapped),
            "edge_count": len(edges),
            "edge_type": "CTRL",
        },
        "nodes": mapped,
        "edges": edges,
        "unmapped": unmapped
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(out_json)
    print(json.dumps(out["meta"], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python tools/build_sbg_ctrl_graph.py <sbg_nodes.json> <joern_calls.tsv> <out.json>")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
