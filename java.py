import copy
import struct


def indent(buf, c):
	ret = ""
	for line in buf.split("\n")[:-1]:
		ret += " "*c + line +"\n"

	return ret
	

class ClassError(Exception):
	pass


class Reader(object):

	def __init__(self, fp):
		self.fp = fp

	def readU16(self):
		return struct.unpack(">H", self.fp.read(2))[0]

	def readU32(self):
		return struct.unpack(">I", self.fp.read(4))[0]

	def read(self, length):
		return self.fp.read(length)


class Constant(object):
	SIZE = 1

	def __init__(self, pool):
		self.pool = pool

	def __repr__(self):
		return str(self)


class NumberConstant(Constant):

	def __init__(self, reader, pool, size):
		super(NumberConstant, self).__init__(pool)
		self.value = reader.read(size)

	def data(self):
		return struct.pack(">c%ds" % (len(self.value), ), self.__class__.TAG, self.value)

	def pretty(self):
		return "%s: %s\n" % (self.__class__.__name__, repr(self.value))

	def update(self, mapping):
		pass

	def __eq__(self, other):
		return self.__class__ == other.__class__ and self.value == other.value

	def __str__(self):
		return "[ %s: %s ]" % (self.__class__.__name__, repr(self.value))


class IntegerConstant(NumberConstant):
	TAG = "\x03"

	def __init__(self, reader, pool):
		super(IntegerConstant, self).__init__(reader, pool, 4)


class FloatConstant(NumberConstant):
	TAG = "\x04"

	def __init__(self, reader, pool):
		super(FloatConstant, self).__init__(reader, pool, 4)


class LongConstant(NumberConstant):
	TAG = "\x05"
	SIZE = 2

	def __init__(self, reader, pool):
		super(LongConstant, self).__init__(reader, pool, 8)


class DoubleConstant(NumberConstant):
	TAG = "\x06"
	SIZE = 2

	def __init__(self, reader, pool):
		super(DoubleConstant, self).__init__(reader, pool, 8)


class RefConstant(Constant):

	def __init__(self, reader, pool):
		super(RefConstant, self).__init__(pool)
		self.classIndex = reader.readU16()
		self.nameAndTypeIndex = reader.readU16()

	def data(self):
		return struct.pack(">cHH", self.__class__.TAG, self.classIndex, self.nameAndTypeIndex)

	def update(self, mapping):
		self.classIndex = mapping[self.classIndex]
		self.nameAndTypeIndex = mapping[self.nameAndTypeIndex]

	def pretty(self):
		return "%s: %d, %d\n" % (self.__class__.__name__, self.classIndex, self.nameAndTypeIndex)

	def __eq__(self, other):
		return self.__class__ == other.__class__ and self.pool[self.classIndex] == other.pool[other.classIndex] and self.pool[self.nameAndTypeIndex] == other.pool[other.nameAndTypeIndex]

	def __str__(self):
		return "[ %s: %d %d ]" % (self.__class__.__name__, self.classIndex, self.nameAndTypeIndex)


class StringConstant(Constant):
	TAG = "\x08"

	def __init__(self, reader, pool):
		super(StringConstant, self).__init__(pool)
		self.stringIndex = reader.readU16()

	def data(self):
		return struct.pack(">cH", self.__class__.TAG, self.stringIndex)

	def update(self, mapping):
		self.stringIndex = mapping[self.stringIndex]

	def pretty(self):
		return "%s: %d\n" % (self.__class__.__name__, self.stringIndex)

	def __eq__(self, other):
		return self.__class__ == other.__class__ and self.pool[self.stringIndex] == other.pool[other.stringIndex]

	def __str__(self):
		return "[ %s: %d ]" % (self.__class__.__name__, self.stringIndex)


class MethodRefConstant(RefConstant):
	TAG = "\x0A"

	def __init__(self, reader, pool):
		super(MethodRefConstant, self).__init__(reader, pool)


class FieldRefConstant(RefConstant):
	TAG = "\x09"

	def __init__(self, reader, pool):
		super(FieldRefConstant, self).__init__(reader, pool)


class InterfaceMethodRefConstant(RefConstant):
	TAG = "\x0B"

	def __init__(self, reader, pool):
		super(InterfaceMethodRefConstant, self).__init__(reader, pool)


class ClassConstant(Constant):
	TAG = "\x07"

	def __init__(self, reader, pool):
		super(ClassConstant, self).__init__(pool)
		self.nameIndex = reader.readU16()

	def data(self):
		return struct.pack(">cH", self.__class__.TAG, self.nameIndex)

	def update(self, mapping):
		self.nameIndex = mapping[self.nameIndex]

	def pretty(self):
		return "%s: %d\n" % (self.__class__.__name__, self.nameIndex)

	def __eq__(self, other):
		return self.__class__ == other.__class__ and self.pool[self.nameIndex] == other.pool[other.nameIndex]

	def __str__(self):
		return "[ %s: %d ]" % (self.__class__.__name__, self.nameIndex)


class Utf8Constant(Constant):
	TAG = "\x01"

	def __init__(self, reader, pool):
		super(Utf8Constant, self).__init__(pool)
		self.length = reader.readU16()
		self.bytes = reader.read(self.length)

	def data(self):
		return struct.pack(">cH", self.__class__.TAG, self.length) + self.bytes

	def update(self, mapping):
		pass

	def pretty(self):
		return "%s: %d '%s'\n" % (self.__class__.__name__, self.length, self.bytes)

	def __eq__(self, other):
		return self.__class__ == other.__class__ and self.length == other.length and self.bytes == other.bytes

	def __str__(self):
		return "[ %s: %d \"%s\" ]" % (self.__class__.__name__, self.length, self.bytes)


class NameAndTypeConstant(Constant):
	TAG = "\x0C"

	def __init__(self, reader, pool):
		super(NameAndTypeConstant, self).__init__(pool)
		self.nameIndex = reader.readU16()
		self.descriptorIndex = reader.readU16()

	def update(self, mapping):
		self.nameIndex = mapping[self.nameIndex]
		self.descriptorIndex = mapping[self.descriptorIndex]

	def data(self):
		return struct.pack(">cHH", self.__class__.TAG, self.nameIndex, self.descriptorIndex)

	def pretty(self):
		return "%s: %d, %d\n" % (self.__class__.__name__, self.nameIndex, self.descriptorIndex)

	def __eq__(self, other):
		return self.__class__ == other.__class__ and self.pool[self.nameIndex] == other.pool[other.nameIndex] and self.pool[self.descriptorIndex] == other.pool[other.descriptorIndex]

	def __str__(self):
		return "[ %s: %d %d ]" % (self.__class__.__name__, self.nameIndex, self.descriptorIndex)


class Field(object):

	def __init__(self, reader, constantPool):
		self.accessFlags = reader.readU16()
		self.nameIndex = reader.readU16()
		self.descriptorIndex = reader.readU16()

		count = reader.readU16()
		self.attributes = []
		for i in xrange(0, count):
			self.attributes.append(Attribute.parse(reader, constantPool))

	def data(self):
		buf = struct.pack(">HHHH", self.accessFlags, self.nameIndex, self.descriptorIndex, len(self.attributes))

		for attribute in self.attributes:
			buf += attribute.data()

		return buf

	def update(self, mapping):
		self.nameIndex = mapping[self.nameIndex]
		self.descriptorIndex = mapping[self.descriptorIndex]

		for attribute in self.attributes:
			attribute.update(mapping)

	def pretty(self):
		buf = "AccessFlags: %d\n" % (self.accessFlags, )
		buf += "NameIndex: %d\n" % (self.nameIndex, )
		buf += "DescriptorIndex: %d\n" % (self.descriptorIndex, )

		buf += "Attributes (%d)\n" % (len(self.attributes, ))
		for attribute in self.attributes:
			buf += indent(attribute.pretty(), 4)

		return buf


class Method(object):

	def __init__(self, reader, constantPool):
		self.accessFlags = reader.readU16()
		self.nameIndex = reader.readU16()
		self.descriptorIndex = reader.readU16()

		count = reader.readU16()
		self.attributes = []
		for i in xrange(0, count):
			self.attributes.append(Attribute.parse(reader, constantPool))

	def data(self):
		buf = struct.pack(">HHHH", self.accessFlags, self.nameIndex, self.descriptorIndex, len(self.attributes))

		for attribute in self.attributes:
			buf += attribute.data()

		return buf

	def update(self, mapping):
		self.nameIndex = mapping[self.nameIndex]
		self.descriptorIndex = mapping[self.descriptorIndex]

		for attribute in self.attributes:
			attribute.update(mapping)

	def pretty(self):
		buf = "AccessFlags: %d\n" % (self.accessFlags, )
		buf += "NameIndex: %d\n" % (self.nameIndex, )
		buf += "DescriptorIndex: %d\n" % (self.descriptorIndex, )

		buf += "Attributes (%d)\n" % (len(self.attributes, ))
		for attribute in self.attributes:
			buf += indent(attribute.pretty(), 4)

		return buf


class Attribute(object):

	@classmethod
	def parse(cls, reader, constantPool):
		nameIndex = reader.readU16()
		constant = constantPool[nameIndex]

		if isinstance(constant, Utf8Constant):
			if constant.bytes == "Code":
				return CodeAttribute(nameIndex, reader, constantPool)
			if constant.bytes == "Signature" or constant.bytes == "SourceFile":
				return SignatureAttribute(nameIndex, reader, constantPool)
			if constant.bytes == "LocalVariableTable" or constant.bytes == "LocalVariableTypeTable":
				return LocalVariableTableAttribute(nameIndex, reader, constantPool)
			if constant.bytes == "LineNumberTable":
				return LineNumberTableAttribute(nameIndex, reader, constantPool)
			if constant.bytes == "Exceptions":
				return ExceptionAttribute(nameIndex, reader, constantPool)
			if constant.bytes == "InnerClasses":
				return InnerClassesAttribute(nameIndex, reader, constantPool)

		return UnknownAttribute(nameIndex, reader, constantPool)


class UnknownAttribute(Attribute):

	def __init__(self, nameIndex, reader, constantPool):
		self.nameIndex = nameIndex
		length = reader.readU32()
		self.rawData = reader.read(length)

	def data(self):
		return struct.pack(">HI", self.nameIndex, len(self.rawData)) + self.rawData

	def update(self, mapping):
		self.nameIndex = mapping[self.nameIndex]

	def pretty(self):
		buf = "NameIndex: %d\n" % (self.nameIndex, )
		buf += "Length: %d\n" % (len(self.rawData), )
		buf += "RawData: %s\n" % (repr(self.rawData), )

		return buf


class ExceptionChild(object):

	def __init__(self, reader):
		self.exceptionIndex = reader.readU16()

	def data(self):
		return struct.pack(">H", self.exceptionIndex)

	def update(self, mapping):
		self.exceptionIndex = mapping[self.exceptionIndex]

	def pretty(self):
		return "ExceptionIndex: %d\n" % (self.exceptionIndex, )


class ExceptionAttribute(Attribute):

	def __init__(self, nameIndex, reader, constantPool):
		self.nameIndex = nameIndex
		self.length = reader.readU32()

		length = reader.readU16()
		self.exceptions = []
		for i in xrange(0, length):
			self.exceptions.append(ExceptionChild(reader))

	def data(self):
		buf = struct.pack(">HIH", self.nameIndex, self.length, len(self.exceptions))
		for exception in self.exceptions:
			buf += exception.data()

		return buf

	def update(self, mapping):
		self.nameIndex = mapping[self.nameIndex]
		for exception in self.exceptions:
			exception.update(mapping)

	def pretty(self):
		buf = "NameIndex: %d\n" % (self.nameIndex, )
		buf += "Length: %d\n" % (self.length, )

		buf += "Exceptions (%d)\n" % (len(self.exceptions), )
		for exception in self.exceptions:
			buf += indent(exception.pretty(), 4)

		return buf


class InnerClass(object):

	def __init__(self, reader):
		self.innerClassInfoIndex = reader.readU16()
		self.outerClassInfoIndex = reader.readU16()
		self.innerNameIndex = reader.readU16()
		self.accessFlags = reader.readU16()

	def data(self):
		return struct.pack(">HHHH", self.innerClassInfoIndex, self.outerClassInfoIndex, self.innerNameIndex, self.accessFlags)

	def update(self, mapping):
		self.innerClassInfoIndex = mapping[self.innerClassInfoIndex]
		self.outerClassInfoIndex = mapping[self.outerClassInfoIndex]
		self.innerNameIndex = mapping[self.innerNameIndex]

	def pretty(self):
		buf = "InnerClassInfoIndex: %d\n" % (self.innerClassInfoIndex, )
		buf += "OuterClassInfoIndex: %d\n" % (self.outerClassInfoIndex, )
		buf += "InnerNameIndex: %d\n" % (self.innerNameIndex, )
		buf += "AccessFlags: %d\n" % (self.accessFlags, )

		return buf


class InnerClassesAttribute(Attribute):

	def __init__(self, nameIndex, reader, constantPool):
		self.nameIndex = nameIndex
		self.length = reader.readU32()

		length = reader.readU16()
		self.classes = []
		for i in xrange(0, length):
			self.classes.append(InnerClass(reader))

	def data(self):
		buf = struct.pack(">HIH", self.nameIndex, self.length, len(self.classes))
		for c in self.classes:
			buf += c.data()

		return buf

	def update(self, mapping):
		self.nameIndex = mapping[self.nameIndex]
		for c in self.classes:
			c.update(mapping)

	def pretty(self):
		buf = "NameIndex: %d\n" % (self.nameIndex, )
		buf += "Length: %d\n" % (self.length, )

		buf += "Classes (%d)\n" % (len(self.classes), )
		for c in self.classes:
			buf += indent(c.pretty(), 4)

		return buf


class ExceptionTableChild(object):

	def __init__(self, reader):
		self.startPc = reader.readU16()
		self.endPc = reader.readU16()
		self.handlerPc = reader.readU16()
		self.catchType = reader.readU16()

	def data(self):
		return struct.pack(">HHHH", self.startPc, self.endPc, self.handlerPc, self.catchType)

	def update(self, mapping):
		self.catchType = mapping[self.catchType]

	def pretty(self):
		buf = "StartPc: %d\n" % (self.startPc, )
		buf += "EndPc: %d\n" % (self.endPc, )
		buf += "HandlerPc: %d\n" % (self.handlerPc, )
		buf += "CatchType: %d\n" % (self.catchType, )

		return buf


class CodeAttribute(Attribute):

	SKIP_TABLE = {
		"\x01": 0,
		"\x02": 0,
		"\x03": 0,
		"\x04": 0,
		"\x05": 0,
		"\x06": 0,
		"\x07": 0,
		"\x08": 0,
		"\x0a": 0,
		"\x10": 1,
		"\x15": 1,
		"\x19": 1,
		"\x1b": 0,
		"\x2a": 0,
		"\x2b": 0,
		"\x2c": 0,
		"\x2d": 0,
		"\x32": 0,
		"\x36": 1,
		"\x3a": 1,
		"\x3b": 0,
		"\x3c": 0,
		"\x3d": 0,
		"\x3e": 0,
		"\x4d": 0,
		"\x4e": 0,
		"\x57": 0,
		"\x59": 0,
		"\x60": 0,
		"\x61": 0,
		"\x64": 0,
		"\x6e": 0,
		"\x6f": 0,
		"\x84": 2,
		"\x85": 0,
		"\x86": 0,
		"\x89": 0,
		"\x8a": 0,
		"\x8d": 0,
		"\x99": 2,
		"\x9a": 2,
		"\x9b": 2,
		"\x9c": 2,
		"\x9d": 2,
		"\x9e": 2,
		"\x9f": 2,
		"\xa0": 2,
		"\xa1": 2,
		"\xa2": 2,
		"\xa3": 2,
		"\xa4": 2,
		"\xa7": 2,
		"\xa8": 2,
		"\xa9": 1,
		"\xac": 0,
		"\xb0": 0,
		"\xb1": 0,
		"\xbc": 0,
		"\xbe": 0,
		"\xbf": 0,
		"\xc6": 2,
		"\xc7": 2,
	}

	def __init__(self, nameIndex, reader, constantPool):
		self.nameIndex = nameIndex
		self.length = reader.readU32() # skip length, we will calculate it when needed
		self.maxStack = reader.readU16()
		self.maxLocals = reader.readU16()
		self.code = reader.read(reader.readU32())
		length = reader.readU16()
		self.exceptionTable = []
		for i in xrange(0, length):
			self.exceptionTable.append(ExceptionTableChild(reader))

		length = reader.readU16()
		self.attributes = []

		for i in xrange(0, length):
			self.attributes.append(Attribute.parse(reader, constantPool))

	def data(self):
		buf = struct.pack(">HIHHI", self.nameIndex, self.length, self.maxStack, self.maxLocals, len(self.code)) + self.code + struct.pack(">H", len(self.exceptionTable))
		for exceptionTableItem in self.exceptionTable:
			buf += exceptionTableItem.data()
		buf += struct.pack(">H", len(self.attributes))
		for attribute in self.attributes:
			buf += attribute.data()

		return buf

	def updateCode(self, code, mapping):
		newCode = ""

		length = len(code)
		i = 0
		while i < length:
			skip = CodeAttribute.SKIP_TABLE.get(code[i])
			if not skip is None:
				newCode += code[i:i + skip + 1]
				i += skip + 1
				continue

			if code[i] == "\x12":
				index = struct.unpack(">B", code[i+1:i+2])[0]
				index = mapping[index]
				newCode += code[i] + struct.pack(">B", index)
				i += 2
				continue

			if code[i] == "\x13" or code[i] == "\x14" or code[i] == "\xb2" or code[i] == "\xb3" or code[i] == "\xb4" or code[i] == "\xb5" or code[i] == "\xb6" or code[i] == "\xb7" or code[i] == "\xb8" or code[i] == "\xbb" or code[i] == "\xc0":
				index = struct.unpack(">H", code[i+1:i+3])[0]
				index = mapping[index]
				newCode += code[i] + struct.pack(">H", index)
				i += 3
				continue

			if code[i] == "\xb9":
				index = struct.unpack(">H", code[i+1:i+3])[0]
				index = mapping[index]
				newCode += code[i] + struct.pack(">H", index) + code[i+3:i+5]
				i += 5
				continue

			break

		if len(newCode) < len(code):
			newCode += code[len(newCode):]

		return newCode

	def update(self, mapping):
		self.nameIndex = mapping[self.nameIndex]

		self.code = self.updateCode(self.code, mapping)

		for attribute in self.attributes:
			attribute.update(mapping)

	def pretty(self):
		buf = "NameIndex: %d\n" % (self.nameIndex, )
		buf += "Length: %d\n" % (self.length, )
		buf += "MaxStack: %d\n" % (self.maxStack, )
		buf += "MaxLocals: %d\n" % (self.maxLocals, )
		buf += "Code: %s\n" % (repr(self.code), )

		buf += "ExceptionTable: (%d)\n" % (len(self.exceptionTable), )
		for exception in self.exceptionTable:
			buf += indent(exception.pretty(), 4)

		buf += "Attributes (%d)\n" % (len(self.attributes), )
		for attribute in self.attributes:
			buf += indent(attribute.pretty(), 4)

		return buf


class LocalVariableTableAttribute(Attribute):

	def __init__(self, nameIndex, reader, constantPool):
		self.nameIndex = nameIndex
		self.length = reader.readU32() # skip length, we will calculate it when needed

		length = reader.readU16()
		self.localVariables = []
		for i in xrange(0, length):
			self.localVariables.append(LocalVariable(reader))

	def data(self):
		buf = struct.pack(">HIH", self.nameIndex, self.length, len(self.localVariables))
		for localVariable in self.localVariables:
			buf += localVariable.data()

		return buf

	def update(self, mapping):
		self.nameIndex = mapping[self.nameIndex]
		for localVariable in self.localVariables:
			localVariable.update(mapping)

	def pretty(self):
		buf = "NameIndex: %d\n" % (self.nameIndex, )
		buf += "Length: %d\n" % (self.length, )

		buf += "LocalVariables (%d)\n" % (len(self.localVariables), )
		for localVariable in self.localVariables:
			buf += indent(localVariable.pretty(), 4)

		return buf


class LineNumber(object):

	def __init__(self, reader):
		self.pc = reader.readU16()
		self.lineNumber = reader.readU16()

	def data(self):
		return struct.pack(">HH", self.pc, self.lineNumber)

	def update(self, lineMapping):
		#self.lineNumber = lineMapping.get(self.lineNumber)
		pass

	def pretty(self):
		buf = "PC: %d\n" % (self.pc, )
		buf += "LineNumber: %d\n" % (self.lineNumber, )

		return buf


class LineNumberTableAttribute(Attribute):

	def __init__(self, nameIndex, reader, constantPool):
		self.nameIndex = nameIndex
		self.length = reader.readU32() # skip length, we will calculate it when needed

		length = reader.readU16()
		self.lineNumbers = []
		for i in xrange(0, length):
			self.lineNumbers.append(LineNumber(reader))

	def data(self):
		buf = struct.pack(">HIH", self.nameIndex, self.length, len(self.lineNumbers))
		for lineNumber in self.lineNumbers:
			buf += lineNumber.data()

		return buf

	def update(self, mapping):
		self.nameIndex = mapping[self.nameIndex]
		for lineNumber in self.lineNumbers:
			lineNumber.update(mapping)

	def pretty(self):
		buf = "NameIndex: %d\n" % (self.nameIndex, )
		buf += "Length: %d\n" % (self.length, )

		buf += "LineNumbers (%d)\n" % (len(self.lineNumbers), )
		for lineNumber in self.lineNumbers:
			buf += indent(lineNumber.pretty(), 4)

		return buf


class SignatureAttribute(Attribute):

	def __init__(self, nameIndex, reader, constantPool):
		self.nameIndex = nameIndex
		reader.readU32() # skip length, we will calculate it when needed
		self.signatureIndex = reader.readU16()

	def data(self):
		return struct.pack(">HIH", self.nameIndex, 2, self.signatureIndex)

	def update(self, mapping):
		self.nameIndex = mapping[self.nameIndex]
		self.signatureIndex = mapping[self.signatureIndex]

	def pretty(self):
		buf = "NameIndex: %d\n" % (self.nameIndex, )
		buf += "Length: %d\n" % (2, )
		buf += "SignatureIndex: %d\n" % (self.signatureIndex, )

		return buf


class SourceFileAttribute(Attribute):

	def __init__(self, nameIndex, reader, constantPool):
		self.nameIndex = nameIndex
		reader.readU32() # skip length, we will calculate it when needed
		self.sourceFileIndex = reader.readU16()

	def data(self):
		return struct.pack(">HIH", self.nameIndex, 2, self.sourceFileIndex)

	def update(self, mapping):
		self.nameIndex = mapping[self.nameIndex]
		self.sourceFileIndex = mapping[self.sourceFileIndex]

	def pretty(self):
		buf = "NameIndex: %d\n" % (self.nameIndex, )
		buf += "Length: %d\n" % (2, )
		buf += "SourceFileIndex: %d\n" % (self.sourceFileIndex, )

		return buf


class LocalVariable(object):

	def __init__(self, reader):
		self.startPc = reader.readU16()
		self.length = reader.readU16()
		self.nameIndex = reader.readU16()
		self.descriptorIndex = reader.readU16()
		self.index = reader.readU16()

	def data(self):
		return struct.pack(">HHHHH", self.startPc, self.length, self.nameIndex, self.descriptorIndex, self.index)

	def update(self, mapping):
		self.nameIndex = mapping[self.nameIndex]
		self.descriptorIndex = mapping[self.descriptorIndex]

	def pretty(self):
		buf = "StartPC: %d\n" % (self.startPc, )
		buf += "Length: %d\n" % (self.length, )
		buf += "NameIndex: %d\n" % (self.nameIndex, )
		buf += "DescriptorIndex: %d\n" % (self.descriptorIndex, )
		buf += "Index: %d\n" % (self.index, )

		return buf

class Class(object):

	CONSTANT_MAP = {
		Utf8Constant.TAG: Utf8Constant,
		IntegerConstant.TAG: IntegerConstant,
		FloatConstant.TAG: FloatConstant,
		LongConstant.TAG: LongConstant,
		DoubleConstant.TAG: DoubleConstant,
		ClassConstant.TAG: ClassConstant,
		StringConstant.TAG: StringConstant,
		FieldRefConstant.TAG: FieldRefConstant,
		MethodRefConstant.TAG: MethodRefConstant,
		InterfaceMethodRefConstant.TAG: InterfaceMethodRefConstant,
		NameAndTypeConstant.TAG: NameAndTypeConstant
	}

	def __init__(self, path):
		self.path = path
		self.constantChange = 0

	def pretty(self):
		buf = "Magic: "+ repr("\xCA\xFE\xBA\xBE") +"\n"
		buf += "Version: %d.%d\n" % (self.version[1] , self.version[0])

		# Constant Pool
		buf += "ConstantPool (%d)\n" % (self.constantPoolSize + self.constantChange, )
		for c in sorted(self.constantPool.keys()):
			buf += indent(self.constantPool[c].pretty(), 4)

		buf += "AccessFlags: %d\n" % (self.accessFlags, )
		buf += "ThisClass: %d\n" % (self.thisClass, )
		buf += "SuperClass: %d\n" % (self.superClass, )

		# Interfaces
		buf += "Interfaces (%d)\n" % (len(self.interfaces, ))
		for interface in self.interfaces:
			buf += indent(interface.pretty(), 4)

		# Fields
		buf += "Fields (%d)\n" % (len(self.fields, ))
		for field in self.fields:
			buf += indent(field.pretty(), 4)

		# Methods
		buf += "Methods (%d)\n" % (len(self.methods, ))
		for method in self.methods:
			buf += indent(method.pretty(), 4)

		# Attributes
		buf += "Attributes (%d)\n" % (len(self.attributes, ))
		for attribute in self.attributes:
			buf += indent(attribute.pretty(), 4)

		return buf

	def findDiffConstants(self, firstPool, secondPool):
		indexes = []
		for i, constant in firstPool.iteritems():
			found = False
			for otherConstant in secondPool.itervalues():
				if constant == otherConstant:
					found = True
					break

			if not found:
				indexes.append(i)

		return indexes

	def diff(self, other):
		# Should really found the minimum number of moves that needs to be done
		# to change selfs constantPool to others constantPool but we start with
		# just handle adds and removes

		mapping = dict([(i, i) for i in xrange(1, self.constantPoolSize + 1)])

		patch = ""

		constantPool = copy.copy(self.constantPool)

		newIndexes = self.findDiffConstants(other.constantPool, self.constantPool)

		delIndexes = self.findDiffConstants(self.constantPool, other.constantPool)

		if delIndexes:
			patch += struct.pack(">BH", 0, len(delIndexes))
			for index in delIndexes:
				patch += struct.pack(">H", index)

				for i in xrange(self.constantPoolSize, 0, -1):
					if mapping[i] <= index:
						break

					mapping[i] -= 1

		if newIndexes:
			patch += struct.pack(">BH", 0, len(newIndexes))
			for index in newIndexes:
				patch += struct.pack(">H", index)

				for i in xrange(self.constantPoolSize, 0, -1):
					if mapping[i] <= index:
						break

					mapping[i] += 1

		self.constantChange = len(newIndexes) - len(delIndexes)

		"""
		for i, constant in enumerate(other.constantPool):
			found = False
			for otherConstant in self.constantPool:
				if constant == otherConstant:
					found = True
					break

			if not found:
				constantPool.insert(i, constant)
				patch += struct.pack(">BH", 0, i) + constant.data()

				for j in xrange(length, 0, -1):
					if mapping[j] <= i:
						break

					mapping[j] += 1
		"""

		with open('patch', 'wb') as fp:
			fp.write(patch)

		for constant in self.constantPool.values():
			constant.update(mapping)

		self.thisClass = mapping[self.thisClass]
		self.superClass = mapping[self.superClass]

		for interface in self.interfaces:
			interface.update(mapping)
		for field in self.fields:
			field.update(mapping)
		for method in self.methods:
			method.update(mapping)
		for attribute in self.attributes:
			attribute.update(mapping)

	def data(self):
		buf = "\xCA\xFE\xBA\xBE"
		buf += struct.pack(">HH", *self.version)

		# Constants
		buf += struct.pack(">H", self.constantPoolSize + self.constantChange)
		for c in sorted(self.constantPool.keys()):
			buf += self.constantPool[c].data()

		buf += struct.pack(">HHH", self.accessFlags, self.thisClass, self.superClass)

		# Interfaces
		buf += struct.pack(">H", len(self.interfaces))
		for interface in self.interfaces:
			buf += interface.data()

		# Fields
		buf += struct.pack(">H", len(self.fields))
		for field in self.fields:
			buf += field.data()

		# Methods
		buf += struct.pack(">H", len(self.methods))
		for method in self.methods:
			buf += method.data()

		# Attributes
		buf += struct.pack(">H", len(self.attributes))
		for attribute in self.attributes:
			buf += attribute.data()

		return buf

	def parse(self):
		with open(self.path) as fp:
			r = Reader(fp)
			if r.read(4) != "\xCA\xFE\xBA\xBE":
				raise ClassError("Wrong magic")

			self.version = struct.unpack(">HH", r.read(4))

			self.constantPoolSize = r.readU16()
			self.constantPool = {}

			i = 1
			while i < self.constantPoolSize:
				type = fp.read(1)
				c = Class.CONSTANT_MAP[type]
				self.constantPool[i] = c(r, self.constantPool)
				i += c.SIZE

			print self.constantPool

			self.accessFlags = r.readU16()
			self.thisClass = r.readU16()
			self.superClass = r.readU16()

			count = r.readU16()
			self.interfaces = []

			for i in xrange(0, count):
				# TODO: Implement
				pass

			count = r.readU16()
			self.fields = []
			for i in xrange(0, count):
				self.fields.append(Field(r, self.constantPool))

			count = r.readU16()
			self.methods = []
			for i in xrange(0, count):
				self.methods.append(Method(r, self.constantPool))

			count = r.readU16()
			self.attributes = []
			for i in xrange(0, count):
				self.attributes.append(Attribute.parse(r, self.constantPool))
