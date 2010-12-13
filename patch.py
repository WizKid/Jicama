import java

org = java.Class("PerFieldAnalyzerWrapper-3.0.2.class")
org.parse()

reference = java.Class("PerFieldAnalyzerWrapper-3.0.3.class")
reference.parse()

#with open("PerFieldAnalyzerWrapper-3.0.3.class.regenerate", "wb") as fp:
#	fp.write(reference.data())

org.diff(reference)

with open("PerFieldAnalyzerWrapper-3.0.2.regenerate.class", "wb") as fp:
	fp.write(org.data())
