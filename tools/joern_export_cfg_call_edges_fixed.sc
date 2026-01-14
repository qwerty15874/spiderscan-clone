import java.nio.file.{Files, Paths}
import java.nio.charset.StandardCharsets

def esc(s: String): String = s.replace("\t"," ").replace("\n"," ").replace("\r"," ")

val cpgPath = "work/pkg1-single/cpg.bin"
val outPath = "results/pkg1/joern_cfg_call_edges.tsv"

importCpg(cpgPath)

def headOrEmpty(t: Iterator[String]): String = if (t.hasNext) t.next() else ""

val header = "src_id\tsrc_name\tsrc_mfn\tsrc_file\tsrc_line\tdst_id\tdst_name\tdst_mfn\tdst_file\tdst_line\n"

val edges =
  cpg.call
    .flatMap { src =>
      val srcId   = src.id.toString
      val srcName = Option(src.name).getOrElse("")
      val srcMfn  = Option(src.methodFullName).getOrElse("")
      val srcFile = headOrEmpty(src.file.name)
      val srcLine = src.lineNumber.getOrElse(-1).toString

      src.cfgNext.isCall.map { dst =>
        val dstId   = dst.id.toString
        val dstName = Option(dst.name).getOrElse("")
        val dstMfn  = Option(dst.methodFullName).getOrElse("")
        val dstFile = headOrEmpty(dst.file.name)
        val dstLine = dst.lineNumber.getOrElse(-1).toString
        s"${esc(srcId)}\t${esc(srcName)}\t${esc(srcMfn)}\t${esc(srcFile)}\t${esc(srcLine)}\t${esc(dstId)}\t${esc(dstName)}\t${esc(dstMfn)}\t${esc(dstFile)}\t${esc(dstLine)}"
      }
    }
    .l
    .distinct

Files.createDirectories(Paths.get(outPath).getParent)
Files.write(Paths.get(outPath), (header + edges.mkString("\n") + "\n").getBytes(StandardCharsets.UTF_8))

println(outPath)
