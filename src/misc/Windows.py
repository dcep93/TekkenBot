import ctypes
import os.path
import sys

# todo test and cleanup
class Windows:
    valid = True
    def __init__(self):
        try:
            from ctypes import wintypes
        except ValueError:
            self.valid = False
            return

        self.wintypes = wintypes
        self.k32 = ctypes.windll.kernel32

        self.OpenProcess = self.k32.OpenProcess
        self.OpenProcess.argtypes = [wintypes.DWORD,ctypes.wintypes.BOOL,ctypes.wintypes.DWORD]
        self.OpenProcess.restype = wintypes.HANDLE

        self.ReadProcessMemory = self.k32.ReadProcessMemory
        self.ReadProcessMemory.argtypes = [wintypes.HANDLE,ctypes.wintypes.LPCVOID,ctypes.wintypes.LPVOID,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
        self.ReadProcessMemory.restype = wintypes.BOOL

        self.GetLastError = self.k32.GetLastError
        self.GetLastError.argtypes = None
        self.GetLastError.restype = wintypes.DWORD

        self.CloseHandle = self.k32.CloseHandle
        self.CloseHandle.argtypes = [wintypes.HANDLE]
        self.CloseHandle.restype = wintypes.BOOL

        self.Psapi = ctypes.WinDLL('Psapi.dll')
        self.EnumProcesses = self.Psapi.EnumProcesses
        self.EnumProcesses.restype = wintypes.BOOL
        self.GetProcessImageFileName = self.Psapi.GetProcessImageFileNameA
        self.GetProcessImageFileName.restype = wintypes.DWORD

    @staticmethod
    def GetModuleAddressByPIDandName(pid, name):
        class MODULEENTRY32(ctypes.Structure):
            _fields_ = [( 'dwSize' , w.wintypes.DWORD ) ,
                        ( 'th32ModuleID' , w.wintypes.DWORD ),
                        ( 'th32ProcessID' , w.wintypes.DWORD ),
                        ( 'GlblcntUsage' , w.wintypes.DWORD ),
                        ( 'ProccntUsage' , w.wintypes.DWORD ) ,
                        ( 'modBaseAddr' , ctypes.POINTER(w.wintypes.BYTE) ) ,
                        ( 'modBaseSize' , w.wintypes.DWORD ) ,
                        ( 'hModule' , w.wintypes.HMODULE ) ,
                        ( 'szModule' , ctypes.c_char * 256 ),
                        ( 'szExePath' , ctypes.c_char * 260 ) ]

        # Establish rights and basic options needed for all process declartion / iteration
        STANDARD_RIGHTS_REQUIRED = 0x000F0000
        SYNCHRONIZE = 0x00100000
        PROCESS_ALL_ACCESS = (STANDARD_RIGHTS_REQUIRED | SYNCHRONIZE | 0xFFF)
        TH32CS_SNAPMODULE = 0x00000008

        me32 = MODULEENTRY32()
        me32.dwSize = ctypes.sizeof(MODULEENTRY32)

        hModuleSnap = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, pid)
        if hModuleSnap == -1:
            print('CreateToolhelp32Snapshot Error [%d]' % w.GetLastError())
            print('Build the code yourself? This is the error for using 32-bit Python. Try the 64-bit version.')

        ret = ctypes.windll.kernel32.Module32First(hModuleSnap, ctypes.pointer(me32) )
        if ret == 0:
            print('ListProcessModules() Error on Module32First[%d]' % w.GetLastError())
            w.CloseHandle(hModuleSnap)

        addressToReturn = None
        while ret:
            if name == me32.szModule.decode("utf-8"):
                addressToReturn = me32.hModule

            ret = ctypes.windll.kernel32.Module32Next(hModuleSnap, ctypes.pointer(me32))
        w.CloseHandle(hModuleSnap)

        return addressToReturn

    @staticmethod
    def GetForegroundPid():
        pid = windows.wintypes.DWORD()
        active = windows.ctypes.windll.user32.GetForegroundWindow()
        active_window = windows.ctypes.windll.user32.GetWindowThreadProcessId(active, windows.ctypes.byref(pid))
        return pid.value

    @staticmethod
    def GetPIDByName(process_name):
        MAX_PATH = 260
        PROCESS_TERMINATE = 0x0001
        PROCESS_QUERY_INFORMATION = 0x0400

        process_name_in_bytes = str.encode(process_name)
        pid = None
        count = 32
        while True:
            process_ids = (w.wintypes.DWORD*count)()
            cb = ctypes.sizeof(process_ids)
            bytes_returned = w.wintypes.DWORD()
            # ???
            if windows.w.EnumProcesses(windows.ctypes.byref(process_ids), cb, windows.ctypes.byref(bytes_returned)):
                if bytes_returned.value < cb:
                    break
                else:
                    count *= 2
            else:
                sys.exit("Call to EnumProcesses failed")

        num_values = int(bytes_returned.value / windows.ctypes.sizeof(windows.wintypes.DWORD))
        for index in range(num_values):
            process_id = process_ids[index]

            h_process = windows.w.OpenProcess(PROCESS_TERMINATE | PROCESS_QUERY_INFORMATION, False, process_id)
            if h_process:
                image_file_name = (windows.ctypes.c_char*MAX_PATH)()
                if windows.w.GetProcessImageFileName(h_process, image_file_name, MAX_PATH)>0:
                    filename = os.path.basename(image_file_name.value)
                    if filename == process_name_in_bytes:
                        pid = process_id
                windows.w.CloseHandle(h_process)
        return pid

w = Windows()
