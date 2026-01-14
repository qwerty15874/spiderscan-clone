import java.nio.file.{Files, Paths}
import java.nio.charset.StandardCharsets

import io.joern.dataflowengineoss.language._

def esc(s: String): String = s.replace("\t"," ").replace("\n"," ").replace("\r"," ")
def headOrEmpty(t: Iterator[String]): String = if (t.hasNext) t.next() else ""

val cpgPath = "work/pkg1-single/cpg.bin"
val outPath = "results/pkg1/joern_dd_call_edges.tsv"
val targetBase = "install.js"

val sensitiveNames = Set(
  "execSync","execFileSync",
  "get","fetch",
  "unzipSync",
  "mkdirSync","writeFileSync","readFileSync",
  "renameSync","unlinkSync","rmdirSync","chmodSync","linkSync","existsSync"
)

importCpg(cpgPath)

val calls =
  cpg.call
    .filter(c => headOrEmpty(c.file.name).endsWith(targetBase))
    .filter(c => sensitiveNames.contains(Option(c.name).getOrElse("")))
    .filter(_.lineNumber.isDefined)
    .map(c => (c.id.toString, Option(c.name).getOrElse(""), Option(c.methodFullName).getOrElse(""),
               headOrEmpty(c.file.name), c.lineNumber.getOrElse(-1)))
    .l
    .sortBy{ case (id,name,_,_,line) => (line, name, id) }

val header =
  "src_id\tsrc_name\tsrc_mfn\tsrc_file\tsrc_line\tdst_id\tdst_name\tdst_mfn\tdst_file\tdst_line\tsink_arg_index\n"

var rows = List[String]()

for (i <- calls.indices) {
  val (sid, sname, smfn, sfile, sline) = calls(i)
  val srcTrav = cpg.call.filter(_.id.toString == sid)

  for (j <- calls.indices) {
    if (i != j) {
      val (did, dname, dmfn, dfile, dline) = calls(j)
      val dstTrav = cpg.call.filter(_.id.toString == did)

      val dstArgs = dstTrav.argument.l
      var argIdx = 0
      dstArgs.foreach { arg =>
        argIdx += 1
        val hasFlow = srcTrav.reachableByFlows(arg).l.nonEmpty
        if (hasFlow) {
          rows = s"${esc(sid)}\t${esc(sname)}\t${esc(smfn)}\t${esc(sfile)}\t${esc(sline.toString)}\t" +
                 s"${esc(did)}\t${esc(dname)}\t${esc(dmfn)}\t${esc(dfile)}\t${esc(dline.toString)}\t${esc(argIdx.toString)}" :: rows
        }
      }
    }
  }
}

val content = header + rows.distinct.reverse.mkString("\n") + "\n"
Files.createDirectories(Paths.get(outPath).getParent)
Files.write(Paths.get(outPath), content.getBytes(StandardCharsets.UTF_8))

println(outPath)
