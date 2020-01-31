import sys
import os.path
import windows

MAX_PATH = 260
PROCESS_TERMINATE = 0x0001
PROCESS_QUERY_INFORMATION = 0x0400

def GetForegroundPid():
    if not windows.valid: return -1
    pid = windows.wintypes.DWORD()
    active = windows.ctypes.windll.user32.GetForegroundWindow()
    active_window = windows.ctypes.windll.user32.GetWindowThreadProcessId(active, windows.ctypes.byref(pid))
    return pid.value

def GetPIDByName(process_name):
    process_name_in_bytes = str.encode(process_name)
    pid = None
    count = 32
    while True:
        process_ids = (windows.wintypes.DWORD*count)()
        cb = windows.ctypes.sizeof(process_ids)
        bytes_returned = windows.wintypes.DWORD()
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
