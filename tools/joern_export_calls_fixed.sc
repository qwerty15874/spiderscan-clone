import java.nio.file.{Files, Paths}
import java.nio.charset.StandardCharsets

def esc(s: String): String = s.replace("\t"," ").replace("\n"," ").replace("\r"," ")

val cpgPath = "work/pkg1-single/cpg.bin"
val outPath = "results/pkg1/joern_calls.tsv"

importCpg(cpgPath)

def headOrEmpty(t: Iterator[String]): String = if (t.hasNext) t.next() else ""

val rows =
  cpg.call
    .map { c =>
      val id = c.id.toString
      val name = Option(c.name).getOrElse("")
      val mfn  = Option(c.methodFullName).getOrElse("")
      val file = headOrEmpty(c.file.name)
      val line = c.lineNumber.getOrElse(-1).toString
      (id, name, mfn, file, line)
    }
    .l

val header = "call_id\tcall_name\tmethod_full_name\tfile\tline\n"
val body = rows.map{ case (id,n,m,f,l) => s"${esc(id)}\t${esc(n)}\t${esc(m)}\t${esc(f)}\t${esc(l)}" }.mkString("\n")
val content = header + body + "\n"

Files.createDirectories(Paths.get(outPath).getParent)
Files.write(Paths.get(outPath), content.getBytes(StandardCharsets.UTF_8))

println(outPath)
