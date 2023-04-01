import os
from utils import globals
from utils.myFileRtns import readNBytes

from utils.ctlFileRtns import myStrToInt
from utils.myFileRtns import removeQuotes

#--------------------------------------------------------------
# The endianness of the TAP file is little endian since the
#   Z80 is so. The M! and ARM processors use big endian 
#   numbers. The following two routines are designed to be
#   endian agnostic and produce appropriat values for 
#   either type machine

#--------------------------------------------------------------
# Make a word value from two bytes
#
# Inputs:
#   bl      low byte
#   bh      high byte
#
# Returns:
#   16 bit value
#
def makeWord(bl, bh):
    return (256 * bh) + bl


#--------------------------------------------------------------
# Make two bytes from a word
#
# Inputs:
#   w       16 bit value
#
# Outputs:
#   bl      low byte
#   bh      high byte
#
def wordToBytes(wd, bytes):
    bytes[0] = wd & 0xFF
    bytes[1] = (wd >> 8) & 0xFF


#--------------------------------------------------------------
# Read the various fields from the TAP header
#
def tapGetHdrLen():
    return makeWord(globals.g_TapHdr[0], globals.g_TapHdr[1])

def tapGetFileType():
    return globals.g_TapHdr[3]

def tapGetFileName():
    fileName = ">"
    for i in range(4, 13):
        fileName = fileName + chr(globals.g_TapHdr[i])
    fileName = fileName + "<"
    return fileName

def tapGetDblkLen():
    return makeWord(globals.g_TapHdr[14], globals.g_TapHdr[15])

def tapGetParam1():
    return makeWord(globals.g_TapHdr[16], globals.g_TapHdr[17])

def tapGetParam2():
    return makeWord(globals.g_TapHdr[18], globals.g_TapHdr[19])


#--------------------------------------------------------------
# Read the header information from a TAP file. 
#
def readTapHdr(fileObj):
# read the binary data from the TAP file header
    globals.g_TapHdr = fileObj.read(0x15)
    tHdrLen = tapGetHdrLen()

# Standard TAP file headers are 0x15 bytes long but
#   nonstandard headers can be longer. We read any 
#   extra bytes and discard them since we cannot use
#   them . See
#   https://sinclair.wiki.zxnet.co.uk/wiki/TAP_format for
#   a longer explanation of the standard header
#
    if(tHdrLen > 0x13):
        junk = fileObj.read(tHdrLen - 0x13)
#        junk = readNBytes(fileObj, tHdrLen - 0x13)

# read the three bytes of the data block header
#    junk = readNBytes(fileObj, 0x03)
    junk = fileObj.read(3)
# the file pointer is now pointing at the start of the data
#   block and we are done

#--------------------------------------------------------------
# Retreive the values from the TAP header to the 
#   global variables
#
def decodeTapInfo():
    globals.g_tapHdrLen = tapGetHdrLen()
    globals.g_tapFileType = tapGetFileType()
    globals.g_tapDBlkLen = tapGetDblkLen()
    globals.g_tapParam1 = tapGetParam1()
    globals.g_tapParam2 = tapGetParam2()
    globals.g_tapFName = tapGetFileName()

    if (globals.g_tapParam1 < 0x8000):
        globals.g_pgmAutoStart = 1



#--------------------------------------------------------------
# Step through a TAP file until we find the desired sub file.
#   If the value in subFileNr is less than 2 or greater than
#   the actual count of sub files, we will return pointing to
#   the first sub file 
#
#   On exit, the TAP file pointer will point to the data section
#   of the desired sub file and the global TAP fields will be
#   updated.
#
def findTapHdr(fileObj, subFileNr):
# ensure we are at the start of the file
    fileObj.seek(0)
    if (subFileNr < 2):
        readTapHdr(fileObj)
        decodeTapInfo()
        return

# get the length of the file
    fileLen = os.path.getsize(globals.g_tapFileName)

    while(True):
    # read a TAP header
        readTapHdr(fileObj)

        if (subFileNr == 1):
            decodeTapInfo()
        # exit if we have found the sub file
            break
    # decrease the sub file number
        subFileNr -= 1

    # get the TAP fields into their globals
        decodeTapInfo()
        fileObj.seek((globals.g_tapDBlkLen + 1), 1)

    # test to see if we are past the end of the file
        if (fileObj.tell() >= fileLen):
            fileObj.seek(0)
            readTapHdr(fileObj)
            decodeTapInfo()
            break


#--------------------------------------------------------------
# Make an AROS chunk map from the user supplied ROM length
#   value
#
def makeArosChunkMap(datLen):
    rtnVal = 0x00

    if(datLen <= 8192):
        rtnVal = 0xEF
    elif(datLen <= (8192 * 2)):
        rtnVal = 0xCF
    elif(datLen <= (8192 * 3)):
        rtnVal = 0x8F
    else:
        rtnVal = 0x0F

    return rtnVal

#--------------------------------------------------------------
# Return the location parameter from a binary file spec
#   in the control file
#
def getBinLoc(binFileName):
    sBinLoc = (binFileName.split(",", 1))
    sLoc = sBinLoc[0]    
    sLoc.strip()
    return myStrToInt(sLoc)

#--------------------------------------------------------------
# Return the file name parameter from a binary file spec
#   in the control file
#
def getBinFileName(binFileName):
    sFName = (binFileName.split(",", 2))
    sf = sFName[1]
    sf = removeQuotes(sf)
    return sf.strip()

#--------------------------------------------------------------
# Make a dock file header from a TAP file bit map byte
#
def makeDockHdr(bitMap):

    globals.g_dockHdr[0] = 0

    globals.g_dockHdr[1] = 0
    globals.g_dockHdr[2] = 0
    globals.g_dockHdr[3] = 0
    globals.g_dockHdr[4] = 0

    if((bitMap & 0x10) == 0):
        globals.g_dockHdr[5] = 2
    if((bitMap & 0x20) == 0):
        globals.g_dockHdr[6] = 2
    if((bitMap & 0x40) == 0):
        globals.g_dockHdr[7] = 2
    if((bitMap & 0x80) == 0):
        globals.g_dockHdr[8] = 2

#--------------------------------------------------------------
# Copy nrBytes from the source file to the destination file.
#   We copy as many as 8192 bytes at a time
#
def fileCpy(srcFileObj, destFileObj, nrBytes):
    
    while (nrBytes > 0):
        if(nrBytes >= 8192):
            # xbuf = bytearray(8192)
            # xBuf = bytearray(srcFileObj.read(8192))
            # destFileObj.write(xBuf)

            fileBuf = srcFileObj.read(8192)
            destFileObj.write(fileBuf)
            nrBytes -= 8192
        else:
            # xbuf = bytearray(nrBytes)
            # xBuf = bytearray(srcFileObj.read(nrBytes))
            # destFileObj.write(xBuf)

            fileBuf = srcFileObj.read(nrBytes)
            destFileObj.write(fileBuf)
            nrBytes = 0




#--------------------------------------------------------------
# Pad a file with the specified number of bytes
#
def padFile(destFileObj, padLen):
    while (padLen != 0):
        if (padLen >= 256):
    # the padLen string is 256 bytes, so we can knock
    #   them out quickly
            destFileObj.write(globals.fillAry)
            padLen -= 256
        else: 
    # write the last few bytes to fill out the padding
            myPad = globals.fillAry[:padLen]
            destFileObj.write(myPad)
            padLen = 0


#--------------------------------------------------------------
# Show the global TAP file variable4s
#
def showTapParams():
    print("TAP parameters:")
    print("g_tapHdrLen: {:04x}".format(globals.g_tapHdrLen))
    print("g_tapFileType: {:02x}".format(globals.g_tapFileType))
    print("g_tapFName: {}".format(globals.g_tapFName))
    print("g_tapDBlkLen: {:04x}".format(globals.g_tapDBlkLen))
    print("g_tapParam1: {:04x}".format(globals.g_tapParam1))
    print("g_tapParam2: {:04x}".format(globals.g_tapParam2))

