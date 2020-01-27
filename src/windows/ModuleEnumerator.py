import sys

import windows

def GetModuleAddressByPIDandName(pid, name):
    class MODULEENTRY32(windows.ctypes.Structure):
        _fields_ = [( 'dwSize' , windows.ctypes.wintypes.DWORD ) ,
                    ( 'th32ModuleID' , windows.ctypes.wintypes.DWORD ),
                    ( 'th32ProcessID' , windows.ctypes.wintypes.DWORD ),
                    ( 'GlblcntUsage' , windows.ctypes.wintypes.DWORD ),
                    ( 'ProccntUsage' , windows.ctypes.wintypes.DWORD ) ,
                    ( 'modBaseAddr' , windows.ctypes.POINTER(windows.ctypes.wintypes.BYTE) ) ,
                    ( 'modBaseSize' , windows.ctypes.wintypes.DWORD ) ,
                    ( 'hModule' , windows.ctypes.wintypes.HMODULE ) ,
                    ( 'szModule' , windows.ctypes.c_char * 256 ),
                    ( 'szExePath' , windows.ctypes.c_char * 260 ) ]

    # Establish rights and basic options needed for all process declartion / iteration
    STANDARD_RIGHTS_REQUIRED = 0x000F0000
    SYNCHRONIZE = 0x00100000
    PROCESS_ALL_ACCESS = (STANDARD_RIGHTS_REQUIRED | SYNCHRONIZE | 0xFFF)
    TH32CS_SNAPMODULE = 0x00000008

    me32 = MODULEENTRY32()
    me32.dwSize = windows.ctypes.sizeof(MODULEENTRY32)

    windll = windows.ctypes.windll

    hModuleSnap = windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, pid)
    if hModuleSnap == -1:
        print('CreateToolhelp32Snapshot Error [%d]' % windows.w.GetLastError())
        print('Build the code yourself? This is the error for using 32-bit Python. Try the 64-bit version.')

    ret = windll.kernel32.Module32First(hModuleSnap, windows.ctypes.pointer(me32) )
    if ret is 0:
        print('ListProcessModules() Error on Module32First[%d]' % windows.w.GetLastError())
        windows.w.CloseHandle(hModuleSnap)

    addressToReturn = None
    while ret:
        if name == me32.szModule.decode("utf-8"):
            addressToReturn = me32.hModule

        ret = windll.kernel32.Module32Next(hModuleSnap, windows.ctypes.pointer(me32))
    windows.w.CloseHandle(hModuleSnap)

    return addressToReturn
