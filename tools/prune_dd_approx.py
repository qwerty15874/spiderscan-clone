import json
import os
import sys

GENERIC_VARS = {
    # 매우 흔한 구문/프로퍼티/프라미스 체인
    "then","catch","finally","on","next","push","shift","resolve","reject",
    "toString","trim","stringify","concat","subarray","fromCharCode",
    # 흔한 식별자
    "error","err","e","res","req","data","buf","buffer","chunks",
    "console","JSON","String","Buffer","Promise",
    # 모듈/별칭(샘플에서 과다 발생)
    "fs","fs2","path","path2","os","os2","https","child_process","zlib",
    # 기타 빈출
    "writeFileSync","readFileSync","mkdirSync","execSync","execFileSync",
    "get","fetch","headers","location",
}

ALLOWED_TRANSITIONS = {
    ("NET","ARCHIVE"), ("NET","FS"), ("NET","PROC"),
    ("ARCHIVE","FS"), ("ARCHIVE","PROC"),
    ("FS","PROC"),
}

def main(in_json: str, out_json: str, out_tsv: str):
    g = json.load(open(in_json, "r", encoding="utf-8"))
    nodes = g["nodes"]
    edges = g["edges"]

    label = {n["id"]: n["label"] for n in nodes}

    kept = []
    for e in edges:
        s = e["src"]; d = e["dst"]
        sl = label.get(s); dl = label.get(d)
        if (sl, dl) not in ALLOWED_TRANSITIONS:
            continue
        rv = [v for v in e.get("reason_vars", []) if v not in GENERIC_VARS]
        if not rv:
            continue
        kept.append({
            **e,
            "reason_vars": rv[:10],
            "src_label": sl,
            "dst_label": dl,
        })

    out = {
        "meta": {
            **g.get("meta", {}),
            "pruned_from": in_json,
            "edge_count_before": len(edges),
            "edge_count_after": len(kept),
            "policy": {
                "allowed_transitions": sorted(list(ALLOWED_TRANSITIONS)),
                "generic_vars_removed": True
            }
        },
        "nodes": nodes,
        "edges": kept
    }

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    json.dump(out, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    os.makedirs(os.path.dirname(out_tsv), exist_ok=True)
    with open(out_tsv, "w", encoding="utf-8") as f:
        f.write("src\tsrc_label\tdst\tdst_label\ttype\treason_vars\n")
        for e in kept:
            f.write(f"{e['src']}\t{e['src_label']}\t{e['dst']}\t{e['dst_label']}\t{e['type']}\t{','.join(e['reason_vars'])}\n")

    print(out_json)
    print(out_tsv)
    print(json.dumps(out["meta"], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python tools/prune_dd_approx.py <in.json> <out.json> <out.tsv>")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
