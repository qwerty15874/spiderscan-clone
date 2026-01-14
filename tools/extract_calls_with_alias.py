import os
import sys

from tree_sitter import Parser, Language
import tree_sitter_javascript as ts_js

try:
    JS = Language(ts_js.language(), "javascript")
except TypeError:
    JS = Language(ts_js.language())

parser = Parser()
parser.language = JS

BUILTIN_HINT = {
    "fs","http","https","child_process","os","path","net","dns","crypto"
}

def extract_text(src: bytes, node):
    return src[node.start_byte:node.end_byte].decode("utf-8", "replace")

def is_require_call(node):
    # require("fs")
    if node.type != "call_expression":
        return False
    # 매우 보수적으로: 텍스트 기반 최소 판정
    return True

def walk(node, fn):
    fn(node)
    for c in node.children:
        walk(c, fn)

def main(js_path: str):
    src = open(js_path, "rb").read()
    tree = parser.parse(src)
    root = tree.root_node

    alias = {}  # alias_name -> module_name

    # 1) require alias 수집: const X = require("mod");
    def collect_alias(n):
        if n.type not in ("lexical_declaration","variable_declaration"):
            return
        t = extract_text(src, n)
        if "require(" not in t:
            return

        # children 기반으로 정확히 잡기: variable_declarator 찾기
        for ch in n.children:
            if ch.type == "variable_declarator":
                ident = None
                call = None
                for vch in ch.children:
                    if vch.type == "identifier":
                        ident = extract_text(src, vch)
                    if vch.type == "call_expression":
                        call = vch
                if not ident or not call:
                    continue
                call_text = extract_text(src, call)
                if not call_text.startswith("require"):
                    continue
                # require("fs")에서 문자열만 뽑기(간단 파서)
                if '"' in call_text:
                    mod = call_text.split('"')[1]
                elif "'" in call_text:
                    mod = call_text.split("'")[1]
                else:
                    continue
                alias[ident] = mod

    walk(root, collect_alias)

    # 2) member call 추출 + alias 적용
    calls = []

    def collect_calls(n):
        if n.type != "call_expression":
            return
        # call_expression 내부에서 member_expression 찾기
        for ch in n.children:
            if ch.type == "member_expression":
                obj = None
                prop = None
                for mch in ch.children:
                    if mch.type == "identifier" and obj is None:
                        obj = extract_text(src, mch)
                    if mch.type in ("property_identifier","identifier"):
                        # property는 보통 뒤쪽에 등장
                        prop = extract_text(src, mch)
                if obj and prop:
                    mod = alias.get(obj, obj)  # alias면 모듈명으로 치환
                    calls.append((f"{mod}.{prop}", n.start_point))

        # 단독 호출(ex: eval(...), exec(...))도 수집(최소)
        # function 자식이 identifier인 call_expression
        if len(n.children) > 0 and n.children[0].type == "identifier":
            fn_name = extract_text(src, n.children[0])
            calls.append((fn_name, n.start_point))

    walk(root, collect_calls)

    print("== file ==")
    print(js_path)
    print("\n== require alias map ==")
    for k,v in alias.items():
        print(f"{k} -> {v}")
    print("\n== calls (after alias resolution) ==")
    for name,(row,col) in calls:
        print(f"{name} @ line {row+1}, col {col+1}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python tools/extract_calls_with_alias.py <js_file>")
    main(sys.argv[1])
