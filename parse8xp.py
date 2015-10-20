# A simple script to convert TI83/84 program files (.8xp) to raw text and back.

import dict_source
import struct
import logging

__author__ = "Spork Interactive"
__version__ = "$Revision: 1.3 $"
__date__ = "$Date: 2009/09/22 $"
__copyright__ = "Copyright (c) 2009 Spork Interactive"
__license__ = "GNU"

_logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

def loadDict (dictType = "compile", options = dict_source.index()):
    ki=0 # ki is the key index
    vi=0 # vi is the value index
    (ki, vi) = {"compile":(1, 0), "decompile":(0, 1), "help":(1, 2)}[dictType]
    d = {}
    # load optional items first
    for item in options:
        # load each optional group
        try:
            m = [(t, "&%s%s" % (item, s.replace("&", "")), h) for (t, s, h) in getattr(dict_source, item)()]
            # We need to correct the dictionary.
            for li in m:
                d[li[ki]] = li[vi]
        except AttributeError:
            _logger.error("%s does not exist!", item)
    for li in dict_source.base():
        #Get the base values
        d[li[ki]] = li[vi]
    if b"" != "":
        # Convert the string literals from unicode to bytes in Python 3.
        # (index 1 are the textual tokens)
        if ki == 1:
            d = dict((k.encode("utf8"), v) for k, v in d.items())
        if vi == 1:
            d = dict((k, v.encode("utf8")) for k, v in d.items())
    return d

def longestKey(dictionary):
    return max([len(k) for k, v in dictionary.items()])

def twoByte(number):
    # Encode a number in little-endian, 0x1234 -> 34 12
    return struct.pack("<H", number & 0xffff)

def stripCRLF(data):
    return data.replace(b"\n", b"").replace(b"\r", b"")

if b"" != "":
    # Python 3
    byte_to_hex = lambda num: num
else:
    byte_to_hex = lambda c: ord(c)

def decompile(source8xp, destination):
    """Decompile a .8xp file, save that to destination file"""
    tDict = loadDict(dictType="decompile")
    maxKeyLen = longestKey(tDict)
    try:
        readFile=open(source8xp, "rb")
        try:
            writeFile=open(destination, "wb")
            try:
                # Load program name, protection type, and comment
                readFile.seek(11, 0)
                comment = readFile.read(42)
                readFile.seek(59, 0)
                protect = readFile.read(1) != b"\x05"
                name = readFile.read(8)
                writeFile.write(name + b"\n")
                if not protect:
                    writeFile.write(b"not ")
                writeFile.write(b"protected\n")
                writeFile.write(comment + b"\n")
                _logger.info("Loading %s...", name)
                _logger.info("Program is %sprotected", protect and "not " or "")
                _logger.info("%s", comment)
                # Find data's end
                readFile.seek(-3, 2)
                fileLength = readFile.tell()
                # Read program meat
                readFile.seek(74, 0)
                while readFile.tell() <= fileLength: # Ignore the last 2 bytes (checksum)
                    readLen = 1 + fileLength - readFile.tell()
                    readLen = min([maxKeyLen, readLen])
                    current = readFile.read(readLen)
                      # Try each possible key for the next few characters
                    while (readLen > 1 and not current in tDict):
                        readFile.seek(-1*readLen, 1)
                        readLen -= 1
                        current = readFile.read(readLen)
                    if current in tDict:
                        writeFile.write(tDict[current])
                        #_logger.debug("%s", tDict[current])
                    else:
                        writeFile.write("&@%s" % current)
                        _logger.warning("character %x not found!", ord(current))
                _logger.info("%s successfully decompiled as %s", source8xp, destination)
            except IOError as e:
                _logger.error("A file error occurred during translation: %s", e)
            finally:
                writeFile.close()
        except IOError as e:
            _logger.error("Error creating %s: %s", destination, e)
        finally:
            readFile.close()
    except IOError as e:
        _logger.error("Error loading %s: %s", source8xp, e)

def recompile(source, destination8xp):
    """Open a text file, compile it as an 8xp.
    The first line should contain the 8 character program name,
    and the second should contain "protected" or "not protected",
    and the third should contain a 42 character comment."""
    tDict = loadDict(dictType="compile")
    maxKeyLen = longestKey(tDict)
    try:
        readFile=open(source, "rb")
        try:
            writeFile=open(destination8xp, "wb")
            try:
                # NOTE: we cannot simply write to file.
                # We have to find the checksum & other crap later
                writeBuffer = []
                # Learn program length
                readFile.seek(-1, 2)
                fileLength = readFile.tell()
                # Skip program name & protection value for now
                readFile.seek(0, 0)
                readFile.readline()
                readFile.readline()
                readFile.readline()
                # Write the opening code
                writeFile.write(b"**TI83F*\x1a\x0a\x00")
                # Read program meat
                lineNum = 4 # line numbers started from 1, and there were 3 lines beforehand.
                while readFile.tell() <= fileLength: # Ignore the last 2 bytes (checksum)
                    readLen = 1 + fileLength - readFile.tell()
                    readLen = min([maxKeyLen, readLen])
                    current = readFile.read(readLen)
                      # Try each possible key for the next few characters
                    while (readLen > 1 and not current in tDict):
                        readFile.seek(-1*readLen, 1)
                        readLen -= 1
                        current = readFile.read(readLen)
                    if current in tDict:
                        writeBuffer.append(tDict[current])
                        if (current == b"\n") or (current == "\r\n"):
                            lineNum += 1
                            # count line numbers
                    elif current == b"&":
                        # The ampersand is the escape sequence character.
                        # If we got here, then:
                        # A) This is the escape sequence &@, indicating that
                        #    the next character should be translated literally.
                        readFile.seek(-1, 1)
                        current = readFile.read(2)
                        if current == b"&@":
                            current = readFile.read(1)
                            writeBuffer.append(current)
                        # B) This is an invalid escape sequence. Let's announce that.
                        else:
                            _logger.warning("%s is an invalid escape sequence on line %d", current, lineNum)
                            writeBuffer.append(b"ERROR " + current)
                    else:
                        # A character is unreadable!
                        _logger.warning("%s not found on line %d", current, lineNum)
                        writeBuffer.append(b"ERROR " + current)
                programMeat = b"".join(writeBuffer)
                # Comment Code
                readFile.seek(0, 0)
                readFile.readline()
                readFile.readline()
                writeFile.write(stripCRLF(readFile.readline()).ljust(42)[:42])
                # After the comment comes the length of program + 19 in two bytes.
                # Note that this would crash if the program were longer than
                # 65536 characters. However, that's more than twice the TI84+ SILVER's
                # memory. Should the limit be exceeded, we've got MUCH BIGGER problems.
                writeFile.write(twoByte(len(programMeat) + 19))
                # Two more unknown characters
                writeFile.write(b"\x0d\x00")
                # Another length for... some... reason...
                writeFile.write(twoByte(len(programMeat) + 2))
                # Now the protection code
                # Protected means it can't be edited once on the calculator
                readFile.seek(0, 0)
                readFile.readline()
                writeFile.write(stripCRLF(readFile.readline())==b"protected\n" and b"\x06" or b"\x05")
                # Now the name
                readFile.seek(0, 0)
                writeFile.write(stripCRLF(readFile.readline()).ljust(8)[:8])
                # Two nulls
                writeFile.write(b"\x00\x00")
                # The length again... same as a few bytes before
                writeFile.write(twoByte(len(programMeat) + 2))
                # And... a different way to write the length of the program.
                writeFile.write(twoByte(len(programMeat)))
                # Now the program
                writeFile.write(programMeat)
                # Checksum - sum of all characters in program
                writeFile.write(twoByte(sum([byte_to_hex(c) for c in programMeat])))
                _logger.info("%s successfully compiled as %s", source, destination8xp)
            except IOError as e:
                _logger.error("A file error occurred during translation: %s", e)
            finally:
                writeFile.close()
        except IOError as e:
            _logger.error("Error creating %s: %s", destination8xp, e)
        finally:
            readFile.close()
    except IOError as e:
        _logger.error("Error loading %s: %s", source, e)

def spellcheck(filename):
    """This function will perform a spell check operation on the indicated file,
    reporting any possible errors. Example: instead of "sin(": sin, SIN("""
    rawize = lambda s: "".join([c for c in s.lower() if ord(c) > 47])
    tDict = loadDict(dictType="help")
    raw = {}
    for k in tDict:
        if len(rawize(k)) > 1:
            raw[rawize(k)] = k
            #This creates a spelling dictionary.
    maxKeyLen = longestKey(tDict)
    try:
        readFile = open(filename, 'r')
        try:
            # This will listize the whole program, then move through it slowly.
            writeBuffer = []
            readFile.seek(-1, 2)
            fileLength = readFile.tell()
            readFile.seek(0, 0)
            readFile.readline()
            readFile.readline()
            readFile.readline()
            lineNum = 4 # line numbers started from 1, and there were 3 lines beforehand.
            while readFile.tell() <= fileLength: # Ignore the last 2 bytes (checksum)
                readLen = 1 + fileLength - readFile.tell()
                readLen = min([maxKeyLen, readLen])
                current = readFile.read(readLen)
                # Try each possible key for the next few characters
                while (readLen > 1 and not current in tDict):
                    readFile.seek(-1*readLen, 1)
                    readLen -= 1
                    current = readFile.read(readLen)
                if current in tDict:
                    writeBuffer.append((current, lineNum))
                    if (current == "\n") or (current == "\r\n"):
                        lineNum += 1
                        # count line numbers
                elif current == "&":
                    # The ampersand is the escape sequence character.
                    # If we got here, then:
                    # A) Someone has used the escape sequence &#, indicating
                    #    that the next character should be translated literally
                    readFile.seek(-1, 1)
                    current = readFile.read(2)
                    if current == "&#":
                        current = readFile.read(1)
                        writeBuffer.append((current, lineNum))
                    # B) This is an invalid escape sequence. Let's announce that.
                    else:
                        _logger.warning("%s is an invalid escape sequence on line %d", current, lineNum)
                        writeBuffer.append((current, lineNum))
                else:
                    # A character is unreadable!
                    writeBuffer.append((current, lineNum))
##                currentraw = rawize(current)
##                # Try each possible key for the next few characters
##                while readLen > 1 and not raw.has_key(rawize(current)):
##                    readFile.seek(-1*readLen, 1)
##                    readLen -= 1
##                    current = readFile.read(readLen)
##                    currentraw = rawize(current)
##                if tDict.has_key(current) and ((current == "\n") or (current == "\r\n")):
##                    lineNum += 1
##                if raw.has_key(currentraw) and len(current) <= len(raw[currentraw]) and (not tDict.has_key(current)) and (not raw[currentraw] == current):
##                    #This is the definition of a spelling error...
##                    _logger.warning("%s '%s'? found on line %d", current, raw[rawize(current)], lineNum)
            _logger.info("File loaded. Analyzing...")
            for item in writeBuffer:
                if rawize(item[0]):
                    i = writeBuffer.index(item)
                    current = ""
                    original = ""
                    #(current, line) = item
                    #full_list = [current, ]
                    # Step 1: Create a chunk
                    while i < len(writeBuffer) and len(current) < maxKeyLen:
                        current = "%s%s" % (current, writeBuffer[i][0])
                        i+=1
                        #full_list.append(current)
                        #_logger.debug("%s", current)
                    # Step 2: Reduce the chunk
                    original = current
                    while current and not current in raw:
                        current = current[:-1]
                    # Step 3: Report.
                    if rawize(current) in raw and original[:len(raw[rawize(current)])] != raw[rawize(current)] and not current in tDict:
                        # A spelling error is a word found misspelled
                        _logger.warning("%s (Line %4d): '%s'", original.replace("\n", " ").replace("\r", "").ljust(maxKeyLen)[:maxKeyLen], item[1], raw[rawize(current)])
        except IOError:
            _logger.error("A file error occurred during translation")
        finally:
            readFile.close()
    except IOError:
        _logger.error("Error loading %s!", filename)

def gethelp(command, results=20):
    """Print help with a command to terminal"""
    tDict = loadDict(dictType="help")
    if command in tDict:
        print(tDict[command] or "No help available")
    else:
        print("%s not found" % command)
        rawize = lambda s: "".join([c for c in s.lower() if ord(c) > 47])
        raw = rawize(command)
        partmatch = lambda s:command in s # Partial match function
        if raw:
            partmatch = lambda s:(raw in rawize(s)) or (command in s)
        matches = 0 # Count the number of matches made so far
        for k, v in tDict.items():
            if partmatch(k):
                matches += 1
                if matches <= results:
                    print("  %s: %s" % (k, v or "No help available"))
        if matches > results:
            print("  *** %s results omitted" % (matches - results))

#if __name__ == "__main__":
#def test():
    #decompile('/Users/cjdd01071/Documents/Analog Clock.8xp', '/Users/cjdd01071/Documents/Clock.txt')
    #decompile('/Users/cjdd01071/Documents/MATHADOR_8.05.06.8xp', '/Users/cjdd01071/Documents/Math.txt')
    #recompile('/Users/cjdd01071/Documents/Math.txt', '/Users/cjdd01071/Documents/Mathtest.8xp')
    #spellcheck('/Users/cjdd01071/Documents/Math.txt')
