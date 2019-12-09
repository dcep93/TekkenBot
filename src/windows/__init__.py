import ctypes

valid = False

class Windows(object):
    def __init__(self):
        self.k32 = ctypes.windll.kernel32

        self.OpenProcess = self.k32.OpenProcess
        self.OpenProcess.argtypes = [ctypes.wintypes.DWORD,ctypes.wintypes.BOOL,ctypes.wintypes.DWORD]
        self.OpenProcess.restype = ctypes.wintypes.HANDLE

        self.ReadProcessMemory = self.k32.ReadProcessMemory
        self.ReadProcessMemory.argtypes = [ctypes.wintypes.HANDLE,ctypes.wintypes.LPCVOID,ctypes.wintypes.LPVOID,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
        self.ReadProcessMemory.restype = ctypes.wintypes.BOOL

        self.GetLastError = self.k32.GetLastError
        self.GetLastError.argtypes = None
        self.GetLastError.restype = ctypes.wintypes.DWORD

        self.CloseHandle = self.k32.CloseHandle
        self.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
        self.CloseHandle.restype = ctypes.wintypes.BOOL

        self.Psapi = ctypes.WinDLL('Psapi.dll')
        self.EnumProcesses = self.Psapi.EnumProcesses
        self.EnumProcesses.restype = ctypes.wintypes.BOOL
        self.GetProcessImageFileName = self.Psapi.GetProcessImageFileNameA
        self.GetProcessImageFileName.restype = ctypes.wintypes.DWORD

try:
    from ctypes import wintypes
    valid = True
    w = Windows()

except ValueError:
    pass
