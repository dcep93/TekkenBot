import ctypes

valid = True

class Windows:
    def __init__(self):
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

try:
    from ctypes import wintypes
except ValueError:
    valid = False
else:
    w = Windows()
