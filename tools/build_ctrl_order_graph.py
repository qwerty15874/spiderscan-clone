import json
import os
import sys

def main(nodes_json: str, out_json: str, k: int = 3):
    data = json.load(open(nodes_json, "r", encoding="utf-8"))
    nodes = data["nodes"]
    nodes_sorted = sorted(nodes, key=lambda x: (x["file"], int(x["line"]), int(x["col"]), x["id"]))

    edges = []
    eid = 1
    for i in range(len(nodes_sorted)):
        a = nodes_sorted[i]
        for step in range(1, k+1):
            j = i + step
            if j >= len(nodes_sorted):
                break
            b = nodes_sorted[j]
            if a["file"] != b["file"]:
                break
            edges.append({
                "id": f"e{eid}",
                "type": "CTRL_ORDER",
                "src": a["id"],
                "dst": b["id"],
                "file": a["file"],
                "step": step
            })
            eid += 1

    out = {
        "meta": {
            "source_nodes": nodes_json,
            "node_count": len(nodes_sorted),
            "edge_count": len(edges),
            "edge_type": "CTRL_ORDER",
            "k": k
        },
        "nodes": nodes_sorted,
        "edges": edges
    }

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    json.dump(out, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(out_json)
    print(json.dumps(out["meta"], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv) not in (3,4):
        raise SystemExit("usage: python tools/build_ctrl_order_graph.py <sbg_nodes.json> <out.json> [k]")
    k = int(sys.argv[3]) if len(sys.argv)==4 else 3
    main(sys.argv[1], sys.argv[2], k)
