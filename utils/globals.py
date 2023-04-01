
import sys
import array

def initGlobals():
    global SENTINEL
    global g_ctlFileName
    global g_tapFileName
    global g_binFileName
    global g_dckFileName

    global g_binFileList


    global g_tapFileType
    global g_tapFName
    global g_tapDBlkLen
    global g_tapParam1
    global g_tapParam2
    global g_tapHdrLen
    global g_pgmAutoStart
    global g_machineCode

# AROS header
    global g_arosType
    global g_arosHdr
    global g_dockHdr
    global g_basStart
    global g_mcVarSize
    global g_subFile
    global g_autoStart

    global g_tapFileObj
    global g_binFileObj
    global g_dckFileObj

    global fillAry


    SENTINEL = "5>Ychs+IhFd[U:q`[tDg`x>[=u=vYFFG"
    g_ctlFileName = ""
    g_tapFileName = ""
    g_binFileName = ""
    g_dckFileName = ""
    g_TapHdr = 0            # buffer for the binary TAP header
    g_arosType = 0
#    g_tapNr = 0
    g_basStart = 0x8008
    g_mcVarSize = 0
    g_subFile = 0
    g_autoStart = 0
    g_binFileList = []

    g_tapHdrLen = 0
    g_tapFileType = 0
    g_tapFName = ""
    g_tapDBlkLen = 0
    g_tapParam1 = 0
    g_tapParam2 = 0
    g_machineCode = 0

    g_pgmAutoStart = 0

    fillAry = bytes(256)

    g_arosHdr = array.array('B', [0, 0, 0, 0, 0, 0, 0, 0])
#    g_arosHdr = bytearray(8)

    g_dockHdr = array.array('B', [0, 0, 0, 0, 0, 0, 0, 0, 0])
#    g_dockHdr = bytearray(10)



