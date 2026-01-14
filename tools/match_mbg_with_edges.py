import json
import sys

TEMPLATES = {
    "T1_NET_ARCHIVE_FS_PROC": ["NET","ARCHIVE","FS","PROC"],
    "T2_NET_FS_PROC": ["NET","FS","PROC"],
    "T3_NET_FS_CHMOD_PROC": ["NET","FS","FS","PROC"],  # chmodSync는 FS라벨로 근사
}

EDGE_OK = {"CTRL_ORDER","DD_APPROX"}

def build_edge_set(edges):
    s = set()
    for e in edges:
        if e.get("type") in EDGE_OK:
            s.add((e["src"], e["dst"]))
    return s

def match_sequence(nodes, labels):
    idxs = []
    i = 0
    for j, n in enumerate(nodes):
        if n["label"] == labels[i]:
            idxs.append(j)
            i += 1
            if i == len(labels):
                return idxs
    return None

def edges_hold(node_ids, edge_set):
    for a, b in zip(node_ids, node_ids[1:]):
        if (a, b) not in edge_set:
            return False
    return True

def main(graph_json, out_json):
    g = json.load(open(graph_json, "r", encoding="utf-8"))
    nodes = g["nodes"]
    nodes_sorted = sorted(nodes, key=lambda x: (x["file"], int(x["line"]), int(x["col"]), x["id"]))
    edge_set = build_edge_set(g.get("edges", []))

    results = []
    for name, seq in TEMPLATES.items():
        idxs = match_sequence(nodes_sorted, seq)
        if not idxs:
            results.append({"template": name, "matched": False, "reason": "no_label_sequence"})
            continue
        picked = [nodes_sorted[k] for k in idxs]
        ids = [n["id"] for n in picked]
        ok = edges_hold(ids, edge_set)
        results.append({
            "template": name,
            "matched": bool(ok),
            "sequence": seq,
            "nodes": picked if ok else picked,
            "reason": "edge_ok" if ok else "edge_missing"
        })

    out = {"meta": {"source_graph": graph_json}, "matches": results}
    json.dump(out, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(out_json)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python tools/match_mbg_with_edges.py <sbg_graph_final.json> <out.json>")
    main(sys.argv[1], sys.argv[2])
