# A simple script to convert TI83/84 program files (.8xp) to raw text and back.

import dict_source

__author__ = "Spork Interactive"
__version__ = "$Revision: 1.3 $"
__date__ = "$Date: 2009/09/22 $"
__copyright__ = "Copyright (c) 2009 Spork Interactive"
__license__ = "GNU"

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
            print "%s does not exist!" % item
    for li in dict_source.base():
        #Get the base values
        d[li[ki]] = li[vi]
    return d

def longestKey(dictionary):
    return max([len(k) for k, v in dictionary.items()])

def twoByte(number):
    return "%s%s" % (chr(number%256), chr((number//256)%256), )

def decompile(source8xp, destination):
    """Decompile a .8xp file, save that to destination file"""
    tDict = loadDict(dictType="decompile")
    maxKeyLen = longestKey(tDict)
    try:
        readFile=open(source8xp, "r")
        try:
            writeFile=open(destination, "w")
            try:
                # Load program name, protection type, and comment
                readFile.seek(11, 0)
                comment = readFile.read(42)
                readFile.seek(59, 0)
                protect = readFile.read(1) == "\x05" and "not " or ""
                name = readFile.read(8)
                writeFile.write("%s\n%sprotected\n%s\n" % (name, protect, comment))
                print "Loading %s..." % name
                print "Program is %sprotected" % protect
                print comment
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
                    while (readLen > 1 and not tDict.has_key(current)):
                        readFile.seek(-1*readLen, 1)
                        readLen -= 1
                        current = readFile.read(readLen)
                    if tDict.has_key(current):
                        writeFile.write(tDict[current])
                        #print tDict[current]
                    else:
                        writeFile.write("&@%s" % current)
                        print "character %s not found!" % hex(ord(current))
                print "%s successfully decompiled as %s" % (source8xp, destination)
            except IOError:
                print "A file error occurred during translation"
            finally:
                writeFile.close()
        except IOError:
            print "Error creating %s!" % destination
        finally:
            readFile.close()
    except IOError:
        print "Error loading %s!" % source8xp

def recompile(source, destination8xp):
    """Open a text file, compile it as an 8xp.
    The first line should contain the 8 character program name,
    and the second should contain "protected" or "not protected",
    and the third should contain a 42 character comment."""
    tDict = loadDict(dictType="compile")
    maxKeyLen = longestKey(tDict)
    try:
        readFile=open(source, "r")
        try:
            writeFile=open(destination8xp, "w")
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
                writeFile.write("**TI83F*\x1a\x0a\x00")
                # Read program meat
                lineNum = 4 # line numbers started from 1, and there were 3 lines beforehand.
                while readFile.tell() <= fileLength: # Ignore the last 2 bytes (checksum)
                    readLen = 1 + fileLength - readFile.tell()
                    readLen = min([maxKeyLen, readLen])
                    current = readFile.read(readLen)
                      # Try each possible key for the next few characters
                    while (readLen > 1 and not tDict.has_key(current)):
                        readFile.seek(-1*readLen, 1)
                        readLen -= 1
                        current = readFile.read(readLen)
                    if tDict.has_key(current):
                        writeBuffer.append(tDict[current])
                        if (current == "\n") or (current == "\r\n"):
                            lineNum += 1
                            # count line numbers
                    elif current == "&":
                        # The ampersand is the escape sequence character.
                        # If we got here, then:
                        # A) This is the escape sequence &@, indicating that
                        #    the next character should be translated literally.
                        readFile.seek(-1, 1)
                        current = readFile.read(2)
                        if current == "&@":
                            current = readFile.read(1)
                            writeBuffer.append(current)
                        # B) This is an invalid escape sequence. Let's announce that.
                        else:
                            print "%s is an invalid escape sequence on line %s" % (current, lineNum)
                            writeBuffer.append("ERROR %s" % current)
                    else:
                        # A character is unreadable!
                        print "%s not found on line &s" % (current, lineNum)
                        writeBuffer.append("ERROR %s" % current)
                programMeat="".join(writeBuffer)
                # Comment Code
                readFile.seek(0, 0)
                readFile.readline()
                readFile.readline()
                writeFile.write(readFile.readline().replace("\n", "").replace("\r", "").ljust(42)[:42])
                # After the comment comes the length of program + 19 in two bytes.
                # Note that this would crash if the program were longer than
                # 65536 characters. However, that's more than twice the TI84+ SILVER's
                # memory. Should the limit be exceeded, we've got MUCH BIGGER problems.
                writeFile.write(twoByte(len(programMeat) + 19))
                # Two more unknown characters
                writeFile.write("\x0d\x00")
                # Another length for... some... reason...
                writeFile.write(twoByte(len(programMeat) + 2))
                # Now the protection code
                # Protected means it can't be edited once on the calculator
                readFile.seek(0, 0)
                readFile.readline()
                writeFile.write(readFile.readline().replace("\n", "").replace("\r", "")=="protected\n" and "\x06" or "\x05")
                # Now the name
                readFile.seek(0, 0)
                writeFile.write(readFile.readline().replace("\n", "").replace("\r", "").ljust(8)[:8])
                # Two nulls
                writeFile.write("\x00\x00")
                # The length again... same as a few bytes before
                writeFile.write(twoByte(len(programMeat) + 2))
                # And... a different way to write the length of the program.
                writeFile.write(twoByte(len(programMeat)))
                # Now the program
                writeFile.write(programMeat)
                # Checksum - sum of all characters in program
                writeFile.write(twoByte(sum([ord(c) for c in programMeat])))
                print "%s successfully compiled as %s" % (source, destination8xp)
            except IOError:
                print "A file error occurred during translation"
            finally:
                writeFile.close()
        except IOError:
            print "Error creating %s!" % destination
        finally:
            readFile.close()
    except IOError:
        print "Error loading %s!" % source8xp

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
                while (readLen > 1 and not tDict.has_key(current)):
                    readFile.seek(-1*readLen, 1)
                    readLen -= 1
                    current = readFile.read(readLen)
                if tDict.has_key(current):
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
                        print "%s is an invalid escape sequence on line %s" % (current, lineNum)
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
##                    print "%s '%s'? found on line %s" % (current, raw[rawize(current)], lineNum)
            print "File loaded. Analyzing..."
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
                        #print current
                    # Step 2: Reduce the chunk
                    original = current
                    while current and not raw.has_key(current):
                        current = current[:-1]
                    # Step 3: Report.
                    if raw.has_key(rawize(current)) and original[:len(raw[rawize(current)])] != raw[rawize(current)] and not tDict.has_key(current):
                        # A spelling error is a word found misspelled
                        print "%s (Line %4d): '%s'" % (original.replace("\n", " ").replace("\r", "").ljust(maxKeyLen)[:maxKeyLen], item[1], raw[rawize(current)])
        except IOError:
            print "A file error occurred during translation"
        finally:
            readFile.close()
    except IOError:
        print "Error loading %s!" % filename

def gethelp(command, results=20):
    """Print help with a command to terminal"""
    tDict = loadDict(dictType="help")
    if tDict.has_key(command):
        print tDict[command] or "No help available"
    else:
        print "%s not found" % command
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
                    print "  %s: %s" % (k, v or "No help available")
        if matches > results:
            print "  *** %s results omitted" % (matches - results)

#if __name__ == "__main__":
#def test():
    #decompile('/Users/cjdd01071/Documents/Analog Clock.8xp', '/Users/cjdd01071/Documents/Clock.txt')
    #decompile('/Users/cjdd01071/Documents/MATHADOR_8.05.06.8xp', '/Users/cjdd01071/Documents/Math.txt')
    #recompile('/Users/cjdd01071/Documents/Math.txt', '/Users/cjdd01071/Documents/Mathtest.8xp')
    #spellcheck('/Users/cjdd01071/Documents/Math.txt')