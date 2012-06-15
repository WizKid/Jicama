import java
import os
import sys

path = sys.argv[1]

if not os.path.exists("old/"+ path) or not os.path.exists("new/"+ path):
    print "Usage %s PATH" % (sys.argv[0], )
    sys.exit(1)

base = os.path.basename(path)

org = java.Class("old/"+ path)
org.parse()

with open(base +".old", "wb") as fp:
    fp.write(org.pretty())

# The new method is 122 bytes not including constant pool changes

reference = java.Class("new/"+ path)
reference.parse()

with open(base +".new", "wb") as fp:
    fp.write(reference.pretty())

#with open("PerFieldAnalyzerWrapper-3.0.3.class.regenerate", "wb") as fp:
#    fp.write(reference.data())

org.diff(reference)

with open(base +".patched", "wb") as fp:
    fp.write(org.pretty())

# print org.pretty()

with open(os.path.basename(path), "wb") as fp:
    fp.write(org.data())
