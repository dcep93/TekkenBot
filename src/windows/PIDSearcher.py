import sys
import os.path
import ctypes
import windows

MAX_PATH = 260
PROCESS_TERMINATE = 0x0001
PROCESS_QUERY_INFORMATION = 0x0400

w = windows.Windows()

def GetForegroundPid():
    if not windows.valid: return None
    pid = ctypes.wintypes.DWORD()
    active = ctypes.windll.user32.GetForegroundWindow()
    active_window = ctypes.windll.user32.GetWindowThreadProcessId(active, ctypes.byref(pid))
    return pid.value

def GetPIDByName(process_name):
    if not windows.valid: return None
    process_name_in_bytes = str.encode(process_name)
    pid = None
    count = 32
    while True:
        process_ids = (windows.wintypes.DWORD*count)()
        cb = ctypes.sizeof(process_ids)
        bytes_returned = windows.wintypes.DWORD()
        # ???
        if w.EnumProcesses(ctypes.byref(process_ids), cb, ctypes.byref(bytes_returned)):
            if bytes_returned.value < cb:
                break
            else:
                count *= 2
        else:
            sys.exit("Call to EnumProcesses failed")

    for index in range(int(bytes_returned.value / ctypes.sizeof(windows.wintypes.DWORD))):
        process_id = process_ids[index]
        # ???
        h_process = w.OpenProcess(PROCESS_TERMINATE | PROCESS_QUERY_INFORMATION, False, process_id)
        if h_process:
            image_file_name = (ctypes.c_char*MAX_PATH)()
            if w.GetProcessImageFileName(h_process, image_file_name, MAX_PATH)>0:
                filename = os.path.basename(image_file_name.value)
                if filename == process_name_in_bytes:
                    pid = process_id
            w.CloseHandle(h_process)
    return pid
