class o(object): pass

try:
    from ctypes import wintypes

    w = wintypes
    
    x = o()
    x.k32 = c.windll.kernel32

    x.OpenProcess = k32.OpenProcess
    x.OpenProcess.argtypes = [w.DWORD,w.BOOL,w.DWORD]
    x.OpenProcess.restype = w.HANDLE

    x.ReadProcessMemory = k32.ReadProcessMemory
    x.ReadProcessMemory.argtypes = [w.HANDLE,w.LPCVOID,w.LPVOID,c.c_size_t,c.POINTER(c.c_size_t)]
    x.ReadProcessMemory.restype = w.BOOL

    x.GetLastError = k32.GetLastError
    x.GetLastError.argtypes = None
    x.GetLastError.restype = w.DWORD

    x.CloseHandle = k32.CloseHandle
    x.CloseHandle.argtypes = [w.HANDLE]
    x.CloseHandle.restype = w.BOOL

    y = o()
    y.Psapi = ctypes.WinDLL('Psapi.dll')
    y.EnumProcesses = Psapi.EnumProcesses
    y.EnumProcesses.restype = ctypes.wintypes.BOOL
    y.GetProcessImageFileName = Psapi.GetProcessImageFileNameA
    y.GetProcessImageFileName.restype = ctypes.wintypes.DWORD

    y.Kernel32 = ctypes.WinDLL('kernel32.dll')
    y.OpenProcess = Kernel32.OpenProcess
    y.OpenProcess.restype = ctypes.wintypes.HANDLE
    y.TerminateProcess = Kernel32.TerminateProcess
    y.TerminateProcess.restype = ctypes.wintypes.BOOL
    y.CloseHandle = Kernel32.CloseHandle

except ValueError:
    pass


