import json
import os
import sys

def main(ctrl_json: str, dd_json: str, out_json: str):
    c = json.load(open(ctrl_json, "r", encoding="utf-8"))
    d = json.load(open(dd_json, "r", encoding="utf-8"))

    nodes = c["nodes"]
    node_ids = {n["id"] for n in nodes}

    edges = []
    seen = set()

    def add_edges(src_edges, prefix):
        nonlocal edges
        for e in src_edges:
            s = e["src"]; t = e["dst"]
            if s not in node_ids or t not in node_ids:
                continue
            k = (s, t, e.get("type",""))
            if k in seen:
                continue
            seen.add(k)
            e2 = dict(e)
            e2["id"] = f"{prefix}{len(edges)+1}"
            edges.append(e2)

    add_edges(c.get("edges", []), "c")
    add_edges(d.get("edges", []), "d")

    out = {
        "meta": {
            "source_ctrl": ctrl_json,
            "source_dd": dd_json,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "edge_types": sorted(list({e.get("type","") for e in edges})),
        },
        "nodes": nodes,
        "edges": edges
    }

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    json.dump(out, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(out_json)
    print(json.dumps(out["meta"], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python tools/merge_graph_edges.py <ctrl.json> <dd.json> <out.json>")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
