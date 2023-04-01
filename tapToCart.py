# main

from pickle import FALSE

import sys
from utils import globals
from utils.myFileRtns import fileExistQ
from utils.myFileRtns import replaceExt
from utils.myFileRtns import getFileExt
from utils.myFileRtns import getFileLen

from utils.tapDckRtns import readTapHdr
from utils.tapDckRtns import wordToBytes
from utils.tapDckRtns import tapGetDblkLen
from utils.tapDckRtns import findTapHdr
from utils.tapDckRtns import showTapParams
from utils.tapDckRtns import makeArosChunkMap
from utils.tapDckRtns import makeDockHdr
from utils.tapDckRtns import getBinLoc
from utils.tapDckRtns import getBinFileName
from utils.tapDckRtns import fileCpy
from utils.tapDckRtns import padFile

from utils.ctlFileRtns import parseCmdFile


#--------------------------------------------------------------
# Main program to get the ball rolling
#
def main():
    print("TAP to cartridge converter V0.1")

    globals.initGlobals()

    if (len(sys.argv) < 2):
        print("No control or TAP file provided")
    else:
        globals.g_ctlFileName = sys.argv[1]
        if(fileExistQ(globals.g_ctlFileName) == True):
    # the file exists, so we can process stuff
            mainExtn = getFileExt(globals.g_ctlFileName)
            if (mainExtn == "tap"):
                doTapOnlyFile()
            else:
                doCtlFile()
            
        else:
            print("Could not find control/TAP file in file system.")
            print(globals.g_ctlFileName)


    input("Press Enter to exit")


#--------------------------------------------------------------
# Make ROM and DCK files from a user supplied TAP file.
#   This function will convert the first subfile into a ROM and
#   DCK file with fixed parameters. There is no way to add
#   binary files to the ROM file.
# 
# See below
#
def doTapOnlyFile():
# save the TAP file name
    globals.g_tapFileName = globals.g_ctlFileName
# make BIN file name
    globals.g_binFileName = replaceExt(globals.g_tapFileName, "bin")

    print(globals.g_binFileName)

# make DCK file name
    globals.g_dckFileName = replaceExt(globals.g_tapFileName, "dck")

# these are default values for a TAP only file
    globals.g_basStart  = 0x8008
    globals.g_mcVarSize = 0
    globals.g_subFile = 1
    globals.g_autoStart = 0

# make the ROM file
    doRomFile()
    padRomFile()
# make the DCK file
    doDckFile()



#--------------------------------------------------------------
# Make ROM and DCK files from the parameters in a user
#   supplied control file
#
def doCtlFile():
# get the parameters from the control file
    if (parseCmdFile() != True):
        print("Error processing control file.")
        print("Exiting program")
        return False

# make the ROM file. this file is required by the
#   succeeding steps
    doRomFile()
# add any binary files to the ROM file
    addBinFiles()
    padRomFile()
# make the DCK file from the ROM file
    doDckFile()



#--------------------------------------------------------------
# This function uses the various global variables to open,
#   process and write a TAP file to disk in ROM format.
#   This function assumes that the TAP file pointer
#   resides at the location of the TAP subfile to
#   be processed
#
def doRomFile():
    print ("doRomFile: {}".format(globals.g_tapFileName))

    rtnVal = False
# determine if the TAP file exists
    rtnVal = fileExistQ(globals.g_tapFileName)
    if (rtnVal == False):
        return rtnVal

# open TAP file
    globals.g_tapFileObj = open(globals.g_tapFileName, "rb")

# get the TAP file 
    findTapHdr(globals.g_tapFileObj, globals.g_subFile)
#    showTapParams()

# this construct is used to allow the wordToBytes function
#   to return two bytes of data. lists are mutable while
#   integers are not.
    bytes = [0, 0]
# make AROS BASIC file header

    globals.g_arosHdr[0] = 1                    # language type: BASIC and possibly machine code
    globals.g_arosHdr[1] = 2                    # cart type: AROS
    wordToBytes(globals.g_basStart, bytes)
    globals.g_arosHdr[2] = bytes[0]             # BASIC start address
    globals.g_arosHdr[3] = bytes[1]             #
    globals.g_arosHdr[4] = makeArosChunkMap(globals.g_tapDBlkLen + 9)

    if (globals.g_pgmAutoStart != 0):
    # the tap file overrides any control file autostart value
        globals.g_arosHdr[5] = 1
    else:
        globals.g_arosHdr[5] = globals.g_autoStart  # auto start spec

    wordToBytes(globals.g_mcVarSize, bytes)
    globals.g_arosHdr[6] = bytes[0]             # reserved bytes
    globals.g_arosHdr[7] = bytes[1]

# open AROS BASIC file
    print(globals.g_binFileName)

    globals.g_binFileObj = open(globals.g_binFileName, "wb")
# save the AROS header
    globals.g_binFileObj.write(globals.g_arosHdr)
# read the TAP file data section
    tapDat = globals.g_tapFileObj.read(globals.g_tapDBlkLen)

# and write to the AROS BIN file
    globals.g_binFileObj.write(tapDat)
    trailer = bytearray(b'\x80')
    globals.g_binFileObj.write(trailer)

    globals.g_binFileObj.close()
    globals.g_tapFileObj.close()


def padRomFile():
    fileLen = getFileLen(globals.g_binFileName)
    padLen = 8192 - (fileLen & 8191)
    if (padLen != 0):
        globals.g_binFileObj = open(globals.g_binFileName, "ab")
        globals.g_binFileObj.seek(fileLen)
        print("padLen: {}".format(padLen))
        padFile(globals.g_binFileObj, padLen)
        globals.g_binFileObj.close()



#--------------------------------------------------------------
# Make a dock file from the ROM file. This function
#   reads the AROS header from the ROM file and
#   generates the DCK header from it. It then writes the
#   DCK header to the file and then copies the ROM
#   file to the new dock file
#
def doDckFile():
    print("Making DCK file")
    print(globals.g_dckFileName)
# open the ROM file and grab the cartridge header
    globals.g_binFileObj = open(globals.g_binFileName, "rb")
    globals.g_arosHdr = globals.g_binFileObj.read(8)

# make the dck header from the chunk map in the bin file
    makeDockHdr(globals.g_arosHdr[4])

# open the dock file
    globals.g_dckFileObj = open(globals.g_dckFileName, "wb")
# go back to the start of the bin file
    globals.g_binFileObj.seek(0)

# write the DCK header to the dock file
    globals.g_dckFileObj.write(globals.g_dockHdr)
# get the size of the binary file
    fileSize = getFileLen(globals.g_binFileName)

    globals.g_binFileObj.seek(0)
# copy the ROM file to the dock file
    fileCpy(globals.g_binFileObj, globals.g_dckFileObj, fileSize)
    
# close both files
    globals.g_binFileObj.close()
    globals.g_dckFileObj.close()

#--------------------------------------------------------------
# Add binary files to the ROM file
#
def addBinFiles():
# are there any binary files
    nrBinFiles = len(globals.g_binFileList)
    if (nrBinFiles == 0):
    # return if there are no binary files to add
        return

# open the ROM file for read/write and get its length
    globals.g_binFileObj = open(globals.g_binFileName, "r+b")
    binFileLen = getFileLen(globals.g_binFileName)
    romFileLoc = binFileLen
# seek to the end of the ROM file
    globals.g_binFileObj.seek(binFileLen)

# loop here for the number of binary files in the control
#   file
    for i in range(0, nrBinFiles):
    # get the file spec for a binary file
        binSpec = globals.g_binFileList[i][1]
    # get the TS memory location for the binary file
        binLoc = getBinLoc(binSpec)
    # compute the offset in the ROM for the binary file
        binOffset = binLoc - 0x8000
    # get the file name for the binary file
        binFileName = getBinFileName(binSpec)

    # ensure the binary file exists
        if(fileExistQ(binFileName) == False):
            globals.g_binFileObj.close()
            print("A binary file does not exist")
            print(binFileName)
            print("Aborting program")
            return
        else:
            print("Processing binary file:")
            print(binFileName)

    # open the binary file and get its length
        srcFileObj = open(binFileName, "rb")
        srcFileLen = getFileLen(binFileName)

    # error out if we are attempting to overwrite previously
    #   allocated memory
        if (binOffset < binFileLen):
            print("Binaray file is overwriting previously used memory.")
            print(binFileName)
            print("Aborting program")
            return
        elif (binOffset > romFileLoc):
    # we need to pad the file to reach the binary address
            padLen = binOffset - romFileLoc
            padFile(globals.g_binFileObj, padLen)
            romFileLoc += padLen

    # write the binary file data to the ROM file
        fileCpy(srcFileObj, globals.g_binFileObj, srcFileLen)
        srcFileObj.close()
        romFileLoc += srcFileLen

# adjust the ROM file AROS chunk map for any added files
    globals.g_binFileObj.seek(0)
    globals.g_arosHdr = bytearray(globals.g_binFileObj.read(8))
    binFileLen = getFileLen(globals.g_binFileName)
    globals.g_arosHdr[4] = makeArosChunkMap(binFileLen)
    globals.g_binFileObj.seek(0)
    globals.g_binFileObj.write(globals.g_arosHdr)
    globals.g_binFileObj.close()




if __name__ == '__main__':
    main()