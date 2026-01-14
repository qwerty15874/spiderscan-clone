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

def main(nodes_json: str, dd_tsv: str, out_json: str):
    data = json.load(open(nodes_json, "r", encoding="utf-8"))
    nodes = data["nodes"]

    # (file_base, line, joern_call_name) -> [node_id]
    idx = defaultdict(list)
    meta = {}
    for n in nodes:
        key = (basename(n["file"]), int(n["line"]), call_to_joern_name(n["call"]))
        idx[key].append(n["id"])
        meta[n["id"]] = n

    edges = []
    seen = set()
    unmapped_rows = 0

    with open(dd_tsv, "r", encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            try:
                sl = int(row["src_line"])
                dl = int(row["dst_line"])
            except Exception:
                continue

            s_key = (basename(row["src_file"]), sl, row["src_name"])
            d_key = (basename(row["dst_file"]), dl, row["dst_name"])

            s_nodes = idx.get(s_key, [])
            d_nodes = idx.get(d_key, [])
            if not s_nodes or not d_nodes:
                unmapped_rows += 1
                continue

            for sid in s_nodes:
                for did in d_nodes:
                    k = (sid, did)
                    if k in seen:
                        continue
                    seen.add(k)
                    edges.append({
                        "id": f"e{len(edges)+1}",
                        "type": "DD",
                        "src": sid,
                        "dst": did,
                        "src_call": meta[sid]["call"],
                        "dst_call": meta[did]["call"],
                    })

    out = {
        "meta": {
            "source_nodes": nodes_json,
            "source_dd_edges": dd_tsv,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "edge_type": "DD",
            "unmapped_dd_rows": unmapped_rows
        },
        "nodes": nodes,
        "edges": edges
    }

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(out_json)
    print(json.dumps(out["meta"], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python tools/build_sbg_dd_graph.py <sbg_nodes.json> <joern_dd_call_edges.tsv> <out.json>")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
