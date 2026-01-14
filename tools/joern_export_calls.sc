import java.nio.file.{Files, Paths}
import java.nio.charset.StandardCharsets

def esc(s: String): String = s.replace("\t"," ").replace("\n"," ").replace("\r"," ")

val cpgPath = cpgFile
val outPath = outTsv

importCpg(cpgPath)

val rows =
  cpg.call
    .map(c => (
      c.id.toString,
      Option(c.name).getOrElse(""),
      Option(c.methodFullName).getOrElse(""),
      Option(c.file.name).getOrElse(""),
      c.lineNumber.getOrElse(-1).toString
    ))
    .l

val header = "call_id\tcall_name\tmethod_full_name\tfile\tline\n"
val body = rows.map{ case (id,n,m,f,l) => s"${esc(id)}\t${esc(n)}\t${esc(m)}\t${esc(f)}\t${esc(l)}" }.mkString("\n")
val content = header + body + "\n"

Files.createDirectories(Paths.get(outPath).getParent)
Files.write(Paths.get(outPath), content.getBytes(StandardCharsets.UTF_8))

println(outPath)
