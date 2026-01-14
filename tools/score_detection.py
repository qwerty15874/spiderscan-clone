import json, sys

def main(report_json):
    r = json.load(open(report_json, "r", encoding="utf-8"))
    out = []
    for m in r["matches"]:
        if not m.get("matched"):
            continue
        labels = [n["label"] for n in m.get("nodes", [])]
        calls  = [n["call"] for n in m.get("nodes", [])]

        score = 0
        reasons = []

        if any(c.startswith("child_process.exec") for c in calls):
            score += 3; reasons.append("PROC(exec*)")
        if any(l=="NET" for l in labels):
            score += 2; reasons.append("NET")
        if any(l=="FS" for l in labels):
            score += 2; reasons.append("FS")
        if any(l=="ARCHIVE" for l in labels):
            score += 2; reasons.append("ARCHIVE")

        domains = []
        for n in m.get("nodes", []):
            domains += n.get("domains", []) or []
        domains = sorted(set(domains))
        if domains:
            score += 3; reasons.append("hardcoded_domain")
        out.append({
            "template": m["template"],
            "score": score,
            "reasons": reasons,
            "domains": domains,
            "nodes": [{"id": n["id"], "call": n["call"], "line": n["line"]} for n in m["nodes"]],
        })

    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: python tools/score_detection.py <detection_report.json>")
    main(sys.argv[1])
