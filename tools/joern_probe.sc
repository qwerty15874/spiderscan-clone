// usage: joern --script tools/joern_probe.sc --params cpgFile=<path>, fileName=<name>, line=<n>

import scala.util.Try

val cpgFile = Try(cpgFile).getOrElse("")
val fileName = Try(fileName).getOrElse("install.js")
val lineNum = Try(line.toInt).getOrElse(148)

println(s"[probe] cpgFile=$cpgFile fileName=$fileName line=$lineNum")

// CPG 로드 방식은 배포에 따라 다를 수 있어, 여기서는 "이미 로드된 cpg" 전제를 피하고
// 네 joern 형태에 맞춰 다음 턴에서 확정한다.
