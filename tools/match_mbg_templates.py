import json
import sys

TEMPLATES = {
    "T1_NET_ARCHIVE_FS_PROC": ["NET", "ARCHIVE", "FS", "PROC"],
    "T2_NET_FS_PROC": ["NET", "FS", "PROC"],
    "T3_FS_CHMOD_PROC": ["FS", "FS", "PROC"],  # chmodSync는 FS 라벨이므로 근사
}

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

def main(nodes_json: str, evidence_json: str, out_json: str):
    nodes = json.load(open(nodes_json, "r", encoding="utf-8"))["nodes"]
    nodes_sorted = sorted(nodes, key=lambda x: (x["file"], x["line"], x["col"], x["id"]))

    evidence = json.load(open(evidence_json, "r", encoding="utf-8"))["evidence"]
    ev_map = {e["id"]: e for e in evidence}

    results = []
    for name, seq in TEMPLATES.items():
        idxs = match_sequence(nodes_sorted, seq)
        if not idxs:
            results.append({"template": name, "matched": False, "sequence": seq})
            continue
        matched_nodes = [nodes_sorted[k] for k in idxs]
        results.append({
            "template": name,
            "matched": True,
            "sequence": seq,
            "nodes": [
                {
                    **n,
                    "snippet": ev_map.get(n["id"], {}).get("snippet"),
                    "urls": ev_map.get(n["id"], {}).get("urls"),
                    "domains": ev_map.get(n["id"], {}).get("domains"),
                    "first_string_arg": ev_map.get(n["id"], {}).get("first_string_arg"),
                }
                for n in matched_nodes
            ]
        })

    out = {
        "meta": {
            "source_nodes": nodes_json,
            "source_evidence": evidence_json,
            "node_count": len(nodes_sorted),
        },
        "template_matches": results
    }
    json.dump(out, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(out_json)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python tools/match_mbg_templates.py <sbg_nodes.json> <verifier_evidence.json> <out.json>")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
