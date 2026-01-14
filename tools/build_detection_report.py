import json
import os
import sys

def load_json(path):
    return json.load(open(path, "r", encoding="utf-8"))

def main(edgeaware_json, evidence_json, out_json):
    m = load_json(edgeaware_json)
    ev = load_json(evidence_json)["evidence"]
    evmap = {x["id"]: x for x in ev}

    reports = []
    for item in m["matches"]:
        nodes = item.get("nodes", [])
        enriched = []
        for n in nodes:
            e = evmap.get(n["id"], {})
            enriched.append({
                **n,
                "snippet": e.get("snippet"),
                "block": e.get("block"),
                "urls": e.get("urls", []),
                "domains": e.get("domains", []),
                "first_string_arg": e.get("first_string_arg"),
            })
        reports.append({**item, "nodes": enriched})

    out = {
        "meta": {
            "source_matches": edgeaware_json,
            "source_evidence": evidence_json,
        },
        "matches": reports
    }

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    json.dump(out, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(out_json)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python tools/build_detection_report.py <mbg_matches_edgeaware.json> <verifier_evidence_v2.json> <out.json>")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
