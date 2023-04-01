import sys
import ntpath
from configparser import SafeConfigParser

from utils import globals

from utils.myFileRtns import replaceExt
from utils.myFileRtns import getFileExt
from utils.myFileRtns import removeQuotes



#--------------------------------------------------------------
# This function converts a string to an integer value.
#   We want to accept hexadecimal strings with a leacing
#   '$' character so the intrnsic Python function cannot
#   be directly used
#
def myStrToInt(sNum):

# assume a decimal radix
    radix = 10
# strip off any leading or trailing whitespace
    myNum = sNum.strip()
# convert the string to lower case
    myNum = myNum.lower()

# replace a leading dollar sign with '0x'
    if(myNum[0] == "$"):
        myNum = myNum[1:len(myNum)]
        myNum = "0x" + myNum

# set the radix to 16 if this is a hex number
    if(myNum[1] == "x"): 
        radix = 16
    return int(myNum, radix)



#--------------------------------------------------------------
# This function parses a command file and sets the parameters
#   to the values contained therein
#
def parseCmdFile():
# activate the INI parser
    parser = SafeConfigParser()
    parser.read(globals.g_ctlFileName)

#----------------------------------------------
# check for the existance and validity of
#   the sentinel
#
    if(parser.has_option("TOP", "sentinel")):
        sentinel = parser.get("TOP", "sentinel")
        if (sentinel != globals.SENTINEL):
            print("Invalid control file")
            return False
    else:
        print("Invalid control file")
        return False

    print("Found a valid control file")


#----------------------------------------------
# Fetch a TAP file spec
#
    if(parser.has_option("TAPFILE", "tapfile")):
        globals.g_tapFileName = parser.get("TAPFILE", "tapfile")
    else:
        print("No TAP file found in control file")
        return False

# remove any leading or trailing quotes from the file name
#   and verify the extension is TAP
    globals.g_tapFileName = removeQuotes(globals.g_tapFileName)
    extn = getFileExt(globals.g_tapFileName)

    if (extn.lower() != "tap"):
        print("BASIC file must be a TAP file with a TAP extension")
        return False


#----------------------------------------------
# Fetch the subfile number, if any
#
    if(parser.has_option("TAPFILE", "subfile")):
        globals.g_subFile = parser.getint("TAPFILE", "subfile")
    else:
    # default value if the option is not present
        globals.g_subFile = 1
# do some minor sanity checking
    if (globals.g_subFile < 1):
        globals.g_subFile = 1

#----------------------------------------------
# Fetch the BASIC start address or set to
#   the default value of 0x8008
#
    if(parser.has_option("HDRDAT", "basStart")):
        sTemp = parser.get("HDRDAT", "basStart")
        globals.g_basStart = myStrToInt(sTemp)
    else:
        globals.g_basStart = 0x8008

#----------------------------------------------
# Fetch the machine code variable space or set
#   to a default value of 0
#
    if(parser.has_option("HDRDAT", "varSpace")):
        sTemp = parser.get("HDRDAT", "varSpace")
        globals.g_mcVarSize = myStrToInt(sTemp)
    else:
        globals.g_mcVarSize = 0x0

#----------------------------------------------
# Fetch the auto start flag or set to zero if
#   not present. This flag will be overridden
#   if the BASIC program in the TAP file 
#   specifies autorun.
#
    if(parser.has_option("HDRDAT", "autoStart")):
        globals.g_autoStart = parser.getint("HDRDAT", "autoStart")
    else:
        globals.g_autoStart = 0


#----------------------------------------------
# Fetch the mixed BASIC/mcode flag or set to zero if
#   not present. 
#
    if(parser.has_option("HDRDAT", "machinecode")):
        globals.g_machineCode = parser.getint("HDRDAT", "machinecode")
    else:
        globals.g_machineCode = 0



#----------------------------------------------
# This section handles the ouput file names
#
    if(parser.has_option("OUTFILES", "binFile")):
        globals.g_binFileName = parser.get("OUTFILES", "binFile")
        globals.g_binFileName = removeQuotes(globals.g_binFileName)
    else:
    # default value
        globals.g_binFileName = replaceExt(globals.g_tapFileName, "bin")

    if(parser.has_option("OUTFILES", "dckFile")):
        globals.g_dckFileName = parser.get("OUTFILES", "dckFile")
        globals.g_dckFileName = removeQuotes(globals.g_dckFileName)
    else:
    # default value
        globals.g_dckFileName = replaceExt(globals.g_tapFileName, "dck")

    print("globals.g_dckFileName")
    print(globals.g_dckFileName)

#----------------------------------------------
# Finally, get any binary file specification
#
    globals.g_binFileList = []
    if(parser.has_section("BINFILES")):
        globals.g_binFileList = parser.items("BINFILES")

    print("Control file processing complete.")

    return True
