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

def load_nodes(nodes_json: str):
    data = json.load(open(nodes_json, "r", encoding="utf-8"))
    nodes = data["nodes"]
    return data, nodes

def main(nodes_json: str, cfg_tsv: str, out_json: str):
    src_data, raw_nodes = load_nodes(nodes_json)

    # 노드 -> 매칭 키 (file_base, line, joern_call_name) -> node_id
    node_index = defaultdict(list)
    node_meta = {}

    for n in raw_nodes:
        want = call_to_joern_name(n["call"])
        key = (basename(n["file"]), int(n["line"]), want)
        node_index[key].append(n["id"])
        node_meta[n["id"]] = n

    edges = []
    seen = set()
    unmapped_cfg = 0

    with open(cfg_tsv, "r", encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            try:
                sl = int(row["src_line"])
                dl = int(row["dst_line"])
            except Exception:
                continue

            s_key = (basename(row["src_file"]), sl, row["src_name"])
            d_key = (basename(row["dst_file"]), dl, row["dst_name"])

            s_nodes = node_index.get(s_key, [])
            d_nodes = node_index.get(d_key, [])
            if not s_nodes or not d_nodes:
                unmapped_cfg += 1
                continue

            # 동일 키에 여러 노드가 있으면(같은 라인 중복 호출 등) 전부 연결
            for sid in s_nodes:
                for did in d_nodes:
                    k = (sid, did)
                    if k in seen:
                        continue
                    seen.add(k)
                    edges.append({
                        "id": f"e{len(edges)+1}",
                        "type": "CTRL_CFG",
                        "src": sid,
                        "dst": did,
                        "src_call": node_meta[sid]["call"],
                        "dst_call": node_meta[did]["call"],
                    })

    out = {
        "meta": {
            "source_nodes": nodes_json,
            "source_cfg_edges": cfg_tsv,
            "node_count": len(raw_nodes),
            "edge_count": len(edges),
            "edge_type": "CTRL_CFG",
            "unmapped_cfg_rows": unmapped_cfg
        },
        "nodes": raw_nodes,
        "edges": edges
    }

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(out_json)
    print(json.dumps(out["meta"], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python tools/build_sbg_cfg_ctrl_graph.py <sbg_nodes.json> <joern_cfg_call_edges.tsv> <out.json>")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
