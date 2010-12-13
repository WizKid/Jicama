import java

org = java.Class("PerFieldAnalyzerWrapper-3.0.2.class")
org.parse()

# print org.pretty()

# The new method is 122 bytes not including constant pool changes

reference = java.Class("PerFieldAnalyzerWrapper-3.0.3.class")
reference.parse()

#print reference.pretty()

#with open("PerFieldAnalyzerWrapper-3.0.3.class.regenerate", "wb") as fp:
#	fp.write(reference.data())

org.diff(reference)

print org.pretty()

with open("PerFieldAnalyzerWrapper-3.0.2.regenerate.class", "wb") as fp:
	fp.write(org.data())

