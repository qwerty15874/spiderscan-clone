const https = require("https");
const fs = require("fs");
const path = require("path");
const os = require("os");
const child_process = require("child_process");

const outDir = path.join(os.tmpdir(), "spiderscan_sim");
const outPath = path.join(outDir, "payload.sh");

// 1) NET: example.com에서 작은 텍스트를 받아온다(무해)
const url = "https://example.com/";

fs.mkdirSync(outDir, { recursive: true });

https.get(url, (res) => {
  let data = "";
  res.on("data", (chunk) => (data += chunk));
  res.on("end", () => {
    // 2) FS: 받아온 데이터를 파일로 기록(무해)
    fs.writeFileSync(outPath, "#!/bin/sh\n" + "echo 'spiderscan sim'\n");
    // 3) FS(chmod): 실행 권한 부여(형태만)
    fs.chmodSync(outPath, 0o755);

    // 4) PROC: 실제로는 다운로드 파일이 아니라, 무해한 node 한 줄 실행만 수행
    child_process.execSync('node -e "console.log(\'spiderscan sim exec\')"', { stdio: "inherit" });
  });
}).on("error", (e) => {
  // 실패해도 FS/PROC 흐름이 깨지지 않게 무해하게 종료
  child_process.execSync('node -e "console.log(\'spiderscan sim net error\')"', { stdio: "inherit" });
});
