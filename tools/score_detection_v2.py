import json, sys, re

SUSP_CMD = re.compile(r"(curl|wget|bash|sh\s|powershell|cmd\.exe|chmod\s*\+x|certutil|bitsadmin)", re.IGNORECASE)
SUSP_PATH = re.compile(r"(/tmp/|/var/tmp/|\.ssh|\.npmrc|AppData|System32|\\Temp\\)", re.IGNORECASE)
TEST_DOMAINS = {"example.com","example.org","example.net","localhost"}

def main(report_json):
    r = json.load(open(report_json, "r", encoding="utf-8"))
    out = []
    for m in r["matches"]:
        if not m.get("matched"):
            continue

        score = 0
        reasons = []

        score += 3; reasons.append("template_matched")

        domains = set()
        urls = set()
        blocks = []
        for n in m.get("nodes", []):
            for d in (n.get("domains") or []):
                domains.add(d)
            for u in (n.get("urls") or []):
                urls.add(u)
            if n.get("block"):
                blocks.append(n["block"])

        if domains or urls:
            score += 3; reasons.append("hardcoded_url_or_domain")

        blob = "\n".join(blocks)
        if blob:
            if SUSP_CMD.search(blob):
                score += 5; reasons.append("suspicious_command_keyword")
            if SUSP_PATH.search(blob):
                score += 4; reasons.append("suspicious_path_keyword")
            # 프로세스 실행 인자(문자열) 존재 여부를 약하게 체크
            if "execSync" in blob or "execFileSync" in blob:
                score += 2; reasons.append("proc_exec_present")

        # 테스트 도메인은 감점
        if any(d in TEST_DOMAINS for d in domains):
            score -= 2; reasons.append("test_domain_penalty")

        verdict = "SUSPICIOUS" if score >= 8 else "LOW_CONFIDENCE"

        out.append({
            "template": m["template"],
            "score": score,
            "verdict": verdict,
            "domains": sorted(domains),
            "urls": sorted(urls),
            "reasons": reasons,
            "nodes": [{"id": n["id"], "call": n["call"], "line": n["line"]} for n in m["nodes"]],
        })

    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: python tools/score_detection_v2.py <detection_report.json>")
    main(sys.argv[1])
