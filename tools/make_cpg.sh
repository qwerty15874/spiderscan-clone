#!/usr/bin/env bash
set -euo pipefail

JOERN_BIN="${JOERN_BIN:-joern}"
IN_DIR="${1:?input dir}"
OUT_CPG="${2:?output cpg path}"

# joern은 보통 'joern --script <sc>' 방식으로 분석을 수행할 수 있다.
# 여기서는 가장 먼저 joern이 실행되는지 확인한다.
"$JOERN_BIN" --help >/dev/null 2>&1 || { echo "joern not runnable: $JOERN_BIN"; exit 2; }

# 실제 CPG 생성은 joern 배포 형태에 따라 'joern-parse' / 'joern' 스크립트 등으로 갈릴 수 있어,
# 다음 단계에서 네 joern 형태에 맞춰 정확히 고정한다.
echo "joern is runnable: $JOERN_BIN"
echo "Input: $IN_DIR"
echo "Target CPG: $OUT_CPG"
