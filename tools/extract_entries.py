import json
import os
import re
import sys

JS_RE = re.compile(r'([A-Za-z0-9_\-./]+\.([cm]?js))')

def find_js_paths_in_script(script: str):
    if not script:
        return []
    return [m.group(1) for m in JS_RE.finditer(script)]

def norm(p: str):
    p = p.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p

def main(pkg_dir: str):
    pj = os.path.join(pkg_dir, "package.json")
    with open(pj, "r", encoding="utf-8") as f:
        data = json.load(f)

    scripts = data.get("scripts", {}) or {}
    install_keys = ["preinstall", "install", "postinstall"]
    install_entries = []
    for k in install_keys:
        v = scripts.get(k)
        for path in find_js_paths_in_script(v or ""):
            install_entries.append(norm(path))

    import_entry = data.get("main")
    if import_entry:
        import_entry = norm(import_entry)

    print("== package ==")
    print(pkg_dir)
    print("\n== install-time entries (from scripts) ==")
    for p in sorted(set(install_entries)):
        print(p)
    print("\n== import-time entry (from main) ==")
    print(import_entry if import_entry else "(none)")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python tools/extract_entries.py <package_dir>")
    main(sys.argv[1])
