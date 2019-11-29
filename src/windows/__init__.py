class o(object): pass

valid = False

try:
    from ctypes import wintypes
    valid = True

except ValueError:
    pass

class Windows(object):
    def __init__(self):
        if not valid: return
        self.k32 = c.windll.kernel32

        self.OpenProcess = k32.OpenProcess
        self.OpenProcess.argtypes = [w.DWORD,w.BOOL,w.DWORD]
        self.OpenProcess.restype = w.HANDLE

        self.ReadProcessMemory = k32.ReadProcessMemory
        self.ReadProcessMemory.argtypes = [w.HANDLE,w.LPCVOID,w.LPVOID,c.c_size_t,c.POINTER(c.c_size_t)]
        self.ReadProcessMemory.restype = w.BOOL

        self.GetLastError = k32.GetLastError
        self.GetLastError.argtypes = None
        self.GetLastError.restype = w.DWORD

        self.CloseHandle = k32.CloseHandle
        self.CloseHandle.argtypes = [w.HANDLE]
        self.CloseHandle.restype = w.BOOL

        self.Psapi = ctypes.WinDLL('Psapi.dll')
        self.EnumProcesses = Psapi.EnumProcesses
        self.EnumProcesses.restype = ctypes.wintypes.BOOL
        self.GetProcessImageFileName = Psapi.GetProcessImageFileNameA
        self.GetProcessImageFileName.restype = ctypes.wintypes.DWORD

        self.Kernel32 = ctypes.WinDLL('kernel32.dll')
        self.OpenProcess = Kernel32.OpenProcess
        self.OpenProcess.restype = ctypes.wintypes.HANDLE
        self.TerminateProcess = Kernel32.TerminateProcess
        self.TerminateProcess.restype = ctypes.wintypes.BOOL
        self.CloseHandle = Kernel32.CloseHandle
