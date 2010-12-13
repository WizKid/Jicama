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

	def __init__(self, tag, pool):
		self.tag = tag
		self.pool = pool

	def __repr__(self):
		return str(self)


class RefConstant(Constant):

	def __init__(self, reader, tag, pool):
		super(RefConstant, self).__init__(tag, pool)
		self.classIndex = reader.readU16()
		self.nameAndTypeIndex = reader.readU16()

	def data(self):
		return struct.pack(">cHH", self.tag, self.classIndex, self.nameAndTypeIndex)

	def update(self, mapping):
		self.classIndex = mapping[self.classIndex]
		self.nameAndTypeIndex = mapping[self.nameAndTypeIndex]

	def pretty(self):
		return "%s: %d, %d\n" % (self.__class__.__name__, self.classIndex, self.nameAndTypeIndex)

	def __eq__(self, other):
		return self.__class__ == other.__class__ and self.pool[self.classIndex - 1] == other.pool[other.classIndex - 1] and self.pool[self.nameAndTypeIndex - 1] == other.pool[other.nameAndTypeIndex - 1]

	def __str__(self):
		return "[ %s: %d %d ]" % (self.__class__.__name__, self.classIndex, self.nameAndTypeIndex)


class StringConstant(Constant):
	TAG = "\x08"

	def __init__(self, reader, pool):
		super(StringConstant, self).__init__(StringConstant.TAG, pool)
		self.stringIndex = reader.readU16()

	def data(self):
		return struct.pack(">cH", self.tag, self.stringIndex)

	def update(self, mapping):
		self.stringIndex = mapping[self.stringIndex]

	def pretty(self):
		return "%s: %d\n" % (self.__class__.__name__, self.stringIndex)

	def __eq__(self, other):
		return self.__class__ == other.__class__ and self.pool[self.stringIndex - 1] == other.pool[other.stringIndex - 1]

	def __str__(self):
		return "[ %s: %d ]" % (self.__class__.__name__, self.stringIndex)


class MethodRefConstant(RefConstant):
	TAG = "\x0A"

	def __init__(self, reader, pool):
		super(MethodRefConstant, self).__init__(reader, MethodRefConstant.TAG, pool)


class FieldRefConstant(RefConstant):
	TAG = "\x09"

	def __init__(self, reader, pool):
		super(FieldRefConstant, self).__init__(reader, FieldRefConstant.TAG, pool)


class InterfaceMethodRefConstant(RefConstant):
	TAG = "\x0B"

	def __init__(self, reader, pool):
		super(InterfaceMethodRefConstant, self).__init__(reader, InterfaceMethodRefConstant.TAG, pool)


class ClassConstant(Constant):
	TAG = "\x07"

	def __init__(self, reader, pool):
		super(ClassConstant, self).__init__(ClassConstant.TAG, pool)
		self.nameIndex = reader.readU16()

	def data(self):
		return struct.pack(">cH", self.tag, self.nameIndex)

	def update(self, mapping):
		self.nameIndex = mapping[self.nameIndex]

	def pretty(self):
		return "%s: %d\n" % (self.__class__.__name__, self.nameIndex)

	def __eq__(self, other):
		return self.__class__ == other.__class__ and self.pool[self.nameIndex - 1] == other.pool[other.nameIndex - 1]

	def __str__(self):
		return "[ %s: %d ]" % (self.__class__.__name__, self.nameIndex)


class Utf8Constant(Constant):
	TAG = "\x01"

	def __init__(self, reader, pool):
		super(Utf8Constant, self).__init__(Utf8Constant.TAG, pool)
		self.length = reader.readU16()
		self.bytes = reader.read(self.length)

	def data(self):
		return struct.pack(">cH", self.tag, self.length) + self.bytes

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
		super(NameAndTypeConstant, self).__init__(NameAndTypeConstant.TAG, pool)
		self.nameIndex = reader.readU16()
		self.descriptorIndex = reader.readU16()

	def update(self, mapping):
		self.nameIndex = mapping[self.nameIndex]
		self.descriptorIndex = mapping[self.descriptorIndex]

	def data(self):
		return struct.pack(">cHH", self.tag, self.nameIndex, self.descriptorIndex)

	def pretty(self):
		return "%s: %d, %d\n" % (self.__class__.__name__, self.nameIndex, self.descriptorIndex)

	def __eq__(self, other):
		return self.__class__ == other.__class__ and self.pool[self.nameIndex - 1] == other.pool[other.nameIndex - 1] and self.pool[self.descriptorIndex - 1] == other.pool[other.descriptorIndex - 1]

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
		constant = constantPool[nameIndex - 1]

		if isinstance(constant, Utf8Constant):
			if constant.bytes == "Code":
				return CodeAttribute(nameIndex, reader, constantPool)
			if constant.bytes == "Signature":
				return SignatureAttribute(nameIndex, reader, constantPool)
			if constant.bytes == "SourceFile":
				return SignatureAttribute(nameIndex, reader, constantPool)
			if constant.bytes == "LocalVariableTable":
				return LocalVariableTableAttribute(nameIndex, reader, constantPool)

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


class CodeAttribute(Attribute):

	SKIP_TABLE = {
		"\x59": 0,
		"\x2a": 0
	}

	def __init__(self, nameIndex, reader, constantPool):
		self.nameIndex = nameIndex
		self.length = reader.readU32() # skip length, we will calculate it when needed
		self.maxStack = reader.readU16()
		self.maxLocals = reader.readU16()
		self.code = reader.read(reader.readU32())
		self.exceptionTableLength = reader.readU16()

		length = reader.readU16()
		self.attributes = []
		for i in xrange(0, length):
			self.attributes.append(Attribute.parse(reader, constantPool))

	def data(self):
		buf = struct.pack(">HIHHI", self.nameIndex, self.length, self.maxStack, self.maxLocals, len(self.code)) + self.code + struct.pack(">HH", self.exceptionTableLength, len(self.attributes))
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

			if code[i] == "\xb2" or code[i] == "\xb4" or code[i] == "\xb6" or code[i] == "\xb7" or code[i] == "\xbb":
				index = struct.unpack(">H", code[i+1:i+3])[0]
				index = mapping[index]
				newCode += code[i] + struct.pack(">H", index)
				i += 3
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
		buf += "ExceptionTableLength: %d\n" % (self.exceptionTableLength, )

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
		ClassConstant.TAG: ClassConstant,
		StringConstant.TAG: StringConstant,
		FieldRefConstant.TAG: FieldRefConstant,
		MethodRefConstant.TAG: MethodRefConstant,
		InterfaceMethodRefConstant.TAG: InterfaceMethodRefConstant,
		NameAndTypeConstant.TAG: NameAndTypeConstant
	}

	def __init__(self, path):
		self.path = path

	def pretty(self):
		buf = "Magic: "+ repr("\xCA\xFE\xBA\xBE") +"\n"
		buf += "Version: %d.%d\n" % (self.version[1] , self.version[0])
		buf += "ConstantPoolLength: %d\n" % (len(self.constantPool), )

		# Constant Pool
		buf += "ConstantPool (%d)\n" % (len(self.constantPool, ))
		for constant in self.constantPool:
			buf += indent(constant.pretty(), 4)

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

	def diff(self, other):
		# Should really found the minimum number of moves that needs to be done
		# to change selfs constantPool to others constantPool but we start with
		# just handle adds and removes

		length = len(self.constantPool)
		mapping = dict([(i, i) for i in xrange(1, length + 1)])

		patch = ""

		constantPool = copy.copy(self.constantPool)

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

		with open('patch', 'wb') as fp:
			fp.write(patch)

		for constant in self.constantPool:
			constant.update(mapping)
		for interface in self.interfaces:
			interface.update(mapping)
		for field in self.fields:
			field.update(mapping)
		for method in self.methods:
			method.update(mapping)
		for attribute in self.attributes:
			attribute.update(mapping)

		self.constantPool = constantPool

	def data(self):
		buf = "\xCA\xFE\xBA\xBE"
		buf += struct.pack(">HH", *self.version)

		# Constants
		buf += struct.pack(">H", len(self.constantPool) +1)
		for constant in self.constantPool:
			buf += constant.data()

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

			count = r.readU16()
			self.constantPool = []

			for i in xrange(1, count):
				type = fp.read(1)
				self.constantPool.append(Class.CONSTANT_MAP[type](r, self.constantPool))

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
