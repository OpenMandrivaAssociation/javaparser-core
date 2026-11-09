Name:		javaparser-core
Version:	3.28.2
Release:	1
Summary:	Java source parser and AST
Group:		Development/Java
License:	(LGPL-3.0-or-later OR Apache-2.0)
URL:		https://github.com/javaparser/javaparser
# The GitHub tag also ships the Maven wrapper jar and prebuilt jars
# under javaparser-symbol-solver-testing. Those are removed from this
# archive. The core module is what this package builds.
Source0:	https://github.com/javaparser/javaparser/archive/refs/tags/javaparser-parent-%{version}.tar.gz#/javaparser-parent-%{version}.tar.gz
# The tag ships the JavaCC grammar, not the generated parser. These
# files are the generated Java sources (no class files).
Source1:	https://repo1.maven.org/maven2/com/github/javaparser/javaparser-core/%{version}/javaparser-core-%{version}-sources.jar
BuildArch:	noarch
BuildRequires:	python
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildSystem:	maven
BuildOption(install):	--file-name %{name}

%description
Parses Java source into an AST, including module descriptors. This
package is the core parser. The JavaCC parser classes are copied from
the upstream sources jar, and JavaParserBuild is filled in during prep.

%prep
%autosetup -n javaparser-javaparser-parent-%{version}
python - <<'PY'
import shutil
import zipfile
from pathlib import Path

core = Path("javaparser-core")
java = core / "src" / "main" / "java"
support = core / "src" / "main" / "javacc-support"
for path in support.rglob("*.java"):
    dest = java / path.relative_to(support)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, dest)

template = core / "src" / "main" / "java-templates" / "com" / "github" / "javaparser" / "JavaParserBuild.java"
text = template.read_text(encoding="utf-8")
text = text.replace("${project.version}", "%{version}")
text = text.replace("${project.name}", "com.github.javaparser:javaparser-core")
text = text.replace("${project.build.finalName}", "javaparser-core-%{version}")
if "${" in text:
    raise SystemExit("JavaParserBuild still has an unfilled property")
build = java / "com" / "github" / "javaparser" / "JavaParserBuild.java"
build.parent.mkdir(parents=True, exist_ok=True)
build.write_text(text, encoding="utf-8")

generated = (
    "com/github/javaparser/AbstractCharStream.java",
    "com/github/javaparser/CharStream.java",
    "com/github/javaparser/GeneratedJavaParser.java",
    "com/github/javaparser/GeneratedJavaParserConstants.java",
    "com/github/javaparser/GeneratedJavaParserTokenManager.java",
    "com/github/javaparser/ParseException.java",
    "com/github/javaparser/Provider.java",
    "com/github/javaparser/SimpleCharStream.java",
    "com/github/javaparser/StreamProvider.java",
    "com/github/javaparser/StringProvider.java",
    "com/github/javaparser/Token.java",
    "com/github/javaparser/TokenMgrException.java",
)
archive = zipfile.ZipFile("%{SOURCE1}")
for name in generated:
    dest = java / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(archive.read(name))
archive.close()

pom = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.github.javaparser</groupId>
  <artifactId>javaparser-core</artifactId>
  <version>%{version}</version>
  <name>com.github.javaparser:javaparser-core</name>
  <description>The core parser functionality.</description>
  <properties>
    <maven.compiler.release>8</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  </properties>
</project>
"""
Path("pom.xml").write_text(pom, encoding="utf-8")
PY
rm -rf src
mv javaparser-core/src src
rm -rf javaparser-core javaparser-core-testing javaparser-core-testing-bdd \
	javaparser-core-generators javaparser-core-metamodel-generator \
	javaparser-core-serialization javaparser-symbol-solver-core \
	javaparser-symbol-solver-testing

%check
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH=$JAVA_HOME/bin:$PATH
mkdir -p check
cat > check/Hello.java <<'END'
package demo;
public class Hello {
	public int n() { return 1; }
}
END
cat > check/Main.java <<'END'
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.body.MethodDeclaration;
import java.io.File;
public class Main {
	public static void main(String[] args) throws Exception {
		java.util.Optional<MethodDeclaration> found = StaticJavaParser.parse(new File("Hello.java"))
			.findFirst(MethodDeclaration.class);
		if (!found.isPresent() || !"n".equals(found.get().getNameAsString())) {
			throw new AssertionError(found.toString());
		}
		System.out.println("javaparser_ok " + found.get().getNameAsString());
	}
}
END
cd check
javac --release 8 -encoding UTF-8 -Xlint:-options \
	-cp ../target/javaparser-core-%{version}.jar -d . Main.java
out=$(java -cp .:../target/javaparser-core-%{version}.jar Main)
echo "$out"
echo "$out" | grep -q javaparser_ok

%files -f .mfiles
%doc LICENSE LICENSE.APACHE LICENSE.GPL LICENSE.LGPL readme.md
