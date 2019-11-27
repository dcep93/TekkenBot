import sys, os.path, ctypes, ctypes.wintypes

Psapi = ctypes.WinDLL('Psapi.dll')
EnumProcesses = Psapi.EnumProcesses
EnumProcesses.restype = ctypes.wintypes.BOOL
GetProcessImageFileName = Psapi.GetProcessImageFileNameA
GetProcessImageFileName.restype = ctypes.wintypes.DWORD

Kernel32 = ctypes.WinDLL('kernel32.dll')
OpenProcess = Kernel32.OpenProcess
OpenProcess.restype = ctypes.wintypes.HANDLE
TerminateProcess = Kernel32.TerminateProcess
TerminateProcess.restype = ctypes.wintypes.BOOL
CloseHandle = Kernel32.CloseHandle

MAX_PATH = 260
PROCESS_TERMINATE = 0x0001
PROCESS_QUERY_INFORMATION = 0x0400

def GetPIDByName(process_name_in_bytes):
    pid = -1
    count = 32
    while True:
        ProcessIds = (ctypes.wintypes.DWORD*count)()
        cb = ctypes.sizeof(ProcessIds)
        BytesReturned = ctypes.wintypes.DWORD()
        if EnumProcesses(ctypes.byref(ProcessIds), cb, ctypes.byref(BytesReturned)):
            if BytesReturned.value<cb:
                break
            else:
                count *= 2
        else:
            sys.exit("Call to EnumProcesses failed")

    for index in range(int(BytesReturned.value / ctypes.sizeof(ctypes.wintypes.DWORD))):
        ProcessId = ProcessIds[index]
        hProcess = OpenProcess(PROCESS_TERMINATE | PROCESS_QUERY_INFORMATION, False, ProcessId)
        if hProcess:
            ImageFileName = (ctypes.c_char*MAX_PATH)()
            if GetProcessImageFileName(hProcess, ImageFileName, MAX_PATH)>0:
                filename = os.path.basename(ImageFileName.value)
                #print(filename)
                if filename == process_name_in_bytes:
                    pid = ProcessId
                    #TerminateProcess(hProcess, 1)
            CloseHandle(hProcess)
    return pid


#print(GetPIDByName(b'TekkenGame-Win64-Shipping.exe'))