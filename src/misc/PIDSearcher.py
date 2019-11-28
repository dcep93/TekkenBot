import sys, os.path, ctypes
import windows

MAX_PATH = 260
PROCESS_TERMINATE = 0x0001
PROCESS_QUERY_INFORMATION = 0x0400

def GetPIDByName(process_name_in_bytes):
    pid = -1
    count = 32
    while True:
        ProcessIds = (windows.wintypes.DWORD*count)()
        cb = ctypes.sizeof(ProcessIds)
        BytesReturned = windows.wintypes.DWORD()
        if EnumProcesses(ctypes.byref(ProcessIds), cb, ctypes.byref(BytesReturned)):
            if BytesReturned.value<cb:
                break
            else:
                count *= 2
        else:
            sys.exit("Call to EnumProcesses failed")

    for index in range(int(BytesReturned.value / ctypes.sizeof(windows.wintypes.DWORD))):
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