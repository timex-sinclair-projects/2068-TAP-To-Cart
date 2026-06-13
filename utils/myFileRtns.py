
import sys
import ntpath
from os.path import exists
from os.path import getsize
import configparser
from utils import globals
#from string import lower


#--------------------------------------------------------------
# This function checks whether a file exists.
#   If so, it retuns True else False.
#
# Return value:
#   True        file exists
#
def fileExistQ(filename):
    if exists(filename):
        rtnVal = True
    else:
        rtnVal = False
    return rtnVal

#--------------------------------------------------------------
# Replace the extension in a file name. The function assumes
#   the last four characters in the file name are a dot and
#   three characters.
#
# Inputs:
#   filename        file name which to replace
#   extension       replacement string
#
# Outputs:
#   filename        the modified file name if successful
#                       the original name if not
# Return value:
#   True        the modified file name or the original
#
#
def replaceExt(filename, extension):
    myFilename = ""
    filename = removeQuotes(filename)
    filenameLen = len(filename)
    if(filename[filenameLen - 4] == "."):
        myFilename = filename[:(filenameLen - 3)] + extension
    else:
        myFilename = filename + "." + extension
    return myFilename

#--------------------------------------------------------------
# Remove all quote characters (0x22) from a string and then
#   trim the string. This does two jobs:
# 1. Removes all quotes from a string
# 2. Strips any leading and trailing quotes from a string
#
def removeQuotes(fileName):
    fName = fileName
    fName = fName.replace(chr(0x22), " ")
    return fName.strip()



#--------------------------------------------------------------
# Return the file extension. This is a dumb routine that
#   expectes the file extension to be the last three
#   characters of the file name.
#
def getFileExt(filename):
    filename = removeQuotes(filename)
    filenameLen = len(filename)
    fileExt = filename[(filenameLen - 3) : filenameLen]
    return fileExt.lower()


#--------------------------------------------------------------
# Wrapper for the getsize() function
#
# Inputs:
#   filename        file path
#
# Returns:
#   file length
#
def getFileLen(fileName):
    return getsize(fileName)


#--------------------------------------------------------------
# Wrapper for the file read function
#
# Inputs:
#   fileObj     file object for a read mode file
#   nrBytes     the number of bytes to read
#
# Returns:
#   the bytes read from the file
#
def readNBytes(fileObj, nrBytes):
    return fileObj.read(nrBytes)

