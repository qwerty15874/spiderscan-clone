import json
import os
import re
import sys
from urllib.parse import urlparse

STR_RE = re.compile(r"""(['"])(?:(?=(\\?))\2.)*?\1""")

def first_string_literal(s: str):
    m = STR_RE.search(s)
    if not m:
        return None
    lit = m.group(0)
    if len(lit) >= 2 and lit[0] in ("'", '"') and lit[-1] == lit[0]:
        return lit[1:-1]
    return None

def all_urls(s: str):
    return re.findall(r"https?://[^\s'\"\)\]]+", s)

def domain_of(url: str):
    try:
        u = urlparse(url)
        return u.hostname
    except Exception:
        return None

def main(blocks_json: str, out_json: str):
    data = json.load(open(blocks_json, "r", encoding="utf-8"))
    nodes = data["nodes"]

    evidence = []
    for n in nodes:
        text = n.get("block") or n.get("snippet") or ""
        urls = all_urls(text)
        domains = [d for d in (domain_of(u) for u in urls) if d]
        arg = first_string_literal(text)

        evidence.append({
            "id": n["id"],
            "call": n["call"],
            "label": n["label"],
            "file": n["file"],
            "line": n["line"],
            "col": n["col"],
            "snippet": n.get("snippet",""),
            "block": text,
            "urls": urls,
            "domains": domains,
            "first_string_arg": arg,
        })

    out = {"meta": {"source": blocks_json, "count": len(evidence)}, "evidence": evidence}
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    json.dump(out, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(out_json)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python tools/build_verifier_evidence_from_blocks.py <verifier_blocks.json> <out.json>")
    main(sys.argv[1], sys.argv[2])
