import sys

import windows

def GetModuleAddressByPIDandName(pid, name):
    class MODULEENTRY32(windows.ctypes.Structure):
        _fields_ = [( 'dwSize' , DWORD ) ,
                    ( 'th32ModuleID' , DWORD ),
                    ( 'th32ProcessID' , DWORD ),
                    ( 'GlblcntUsage' , DWORD ),
                    ( 'ProccntUsage' , DWORD ) ,
                    ( 'modBaseAddr' , POINTER(BYTE) ) ,
                    ( 'modBaseSize' , DWORD ) ,
                    ( 'hModule' , HMODULE ) ,
                    ( 'szModule' , c_char * 256 ),
                    ( 'szExePath' , c_char * 260 ) ]
    # const variable
    # Establish rights and basic options needed for all process declartion / iteration
    TH32CS_SNAPPROCESS = 2
    STANDARD_RIGHTS_REQUIRED = 0x000F0000
    SYNCHRONIZE = 0x00100000
    PROCESS_ALL_ACCESS = (STANDARD_RIGHTS_REQUIRED | SYNCHRONIZE | 0xFFF)
    TH32CS_SNAPMODULE = 0x00000008
    TH32CS_SNAPTHREAD = 0x00000004


    CreateToolhelp32Snapshot= windll.kernel32.CreateToolhelp32Snapshot
    Process32First = windll.kernel32.Process32First
    Process32Next = windll.kernel32.Process32Next
    Module32First = windll.kernel32.Module32First
    Module32Next = windll.kernel32.Module32Next
    GetLastError = windll.kernel32.GetLastError
    OpenProcess = windll.kernel32.OpenProcess
    GetPriorityClass = windll.kernel32.GetPriorityClass
    CloseHandle = windll.kernel32.CloseHandle


    try:
        addressToReturn = None

        ProcessID=pid
        hModuleSnap = DWORD
        me32 = MODULEENTRY32()
        me32.dwSize = sizeof( MODULEENTRY32 )
        #me32.dwSize = 5000

        hModuleSnap = CreateToolhelp32Snapshot( TH32CS_SNAPMODULE, ProcessID )
        if hModuleSnap == -1:
            print('CreateToolhelp32Snapshot Error [%d]' % GetLastError())
            print('Build the code yourself? This is the error for using 32-bit Python. Try the 64-bit version.')

        ret = Module32First( hModuleSnap, pointer(me32) )
        if ret == 0 :
            print('ListProcessModules() Error on Module32First[%d]' % GetLastError())
            CloseHandle( hModuleSnap )
        PROGMainBase = False
        while ret :
            #print(me32.dwSize)
            #print(me32.th32ModuleID)
            #print(me32.th32ProcessID)
            #print(me32.GlblcntUsage)
            #print(me32.ProccntUsage)
            #print(me32.modBaseAddr)
            #print(me32.modBaseSize)
            #print(me32.hModule)
            #print(me32.szModule)
            #print(me32.szExePath)
            #print(name == me32.szModule.decode("utf-8"))
            if name == me32.szModule.decode("utf-8"):
                addressToReturn = me32.hModule
                #print(me32.modBaseAddr.value)

            ret = Module32Next( hModuleSnap , pointer(me32) )
        CloseHandle( hModuleSnap )

        return addressToReturn

    except:
        print("Error in ListProcessModules")
        raise
