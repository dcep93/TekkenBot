from ..misc import w_windows

import ctypes
import os.path
import sys
import time
import typing

class Windows:
    def __init__(self) -> None:
        self.valid = w_windows.valid
        if not self.valid:
            return

        w_windows.windll.shcore.SetProcessDpiAwareness(1)

        self.k32 = w_windows.windll.kernel32

        self.open_process = self.k32.OpenProcess
        self.open_process.argtypes = [w_windows.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD]
        self.open_process.restype = w_windows.wintypes.HANDLE

        self.read_process_memory = self.k32.ReadProcessMemory
        self.read_process_memory.argtypes = [w_windows.wintypes.HANDLE, ctypes.wintypes.LPCVOID, ctypes.wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        self.read_process_memory.restype = w_windows.wintypes.BOOL

        self.get_last_error = self.k32.GetLastError
        self.get_last_error.argtypes = None
        self.get_last_error.restype = w_windows.wintypes.DWORD

        self.close_handle = self.k32.CloseHandle
        self.close_handle.argtypes = [w_windows.wintypes.HANDLE]
        self.close_handle.restype = w_windows.wintypes.BOOL

        psapi = ctypes.WinDLL('Psapi.dll')
        self.enum_processes = psapi.EnumProcesses
        self.enum_processes.restype = w_windows.wintypes.BOOL
        self.get_process_image_filename = psapi.GetProcessImageFileNameA
        self.get_process_image_filename.restype = w_windows.wintypes.DWORD

    def get_module_address(self, pid: int, name: str) -> typing.Optional[int]:
        class ModuleEntry(ctypes.Structure):
            _fields_ = [('dwSize', w_windows.wintypes.DWORD),
                        ('th32ModuleID', w_windows.wintypes.DWORD),
                        ('th32ProcessID', w_windows.wintypes.DWORD),
                        ('GlblcntUsage', w_windows.wintypes.DWORD),
                        ('ProccntUsage', w_windows.wintypes.DWORD),
                        ('modBaseAddr', ctypes.POINTER(w_windows.wintypes.BYTE)),
                        ('modBaseSize', w_windows.wintypes.DWORD),
                        ('hModule', w_windows.wintypes.HMODULE),
                        ('szModule', ctypes.c_char * 256),
                        ('szExePath', ctypes.c_char * 260)]

        # Establish rights and basic options needed for all process declartion / iteration
        TH32CS_SNAPMODULE = 0x00000008

        me32 = ModuleEntry()
        me32.dwSize = ctypes.sizeof(ModuleEntry)

        h_module_snap = w_windows.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, pid)
        if h_module_snap == -1:
            print('CreateToolhelp32Snapshot Error [%d]' % self.get_last_error())
            print('Build the code yourself? This is the error for using 32-bit Python. Try the 64-bit version.')

        ret = w_windows.windll.kernel32.Module32First(h_module_snap, ctypes.pointer(me32))
        if ret == 0:
            print('ListProcessModules() Error on Module32First[%d]' % self.get_last_error())
            self.close_handle(h_module_snap)

        address_to_return = None
        while ret:
            if name == me32.szModule.decode("utf-8"):
                address_to_return = me32.hModule

            ret = w_windows.windll.kernel32.Module32Next(h_module_snap, ctypes.pointer(me32))
        self.close_handle(h_module_snap)

        return address_to_return

    def get_foreground_pid(self) -> int:
        pid = w_windows.wintypes.DWORD()
        active = w_windows.windll.user32.GetForegroundWindow()
        w_windows.windll.user32.GetWindowThreadProcessId(active, ctypes.byref(pid))
        assert(isinstance(pid.value, int))
        return pid.value

    def get_pid(self, process_name: str) -> typing.Optional[int]:
        MAX_PATH = 260
        PROCESS_TERMINATE = 0x0001
        PROCESS_QUERY_INFORMATION = 0x0400

        process_name_in_bytes = str.encode(process_name)
        pid = None
        count = 32
        for _ in range(10000):
            process_ids = (w_windows.wintypes.DWORD*count)()
            cb = ctypes.sizeof(process_ids)
            bytes_returned = w_windows.wintypes.DWORD()
            # ???
            if self.enum_processes(ctypes.byref(process_ids), cb, ctypes.byref(bytes_returned)):
                if bytes_returned.value < cb:
                    break
                count *= 2
            else:
                raise Exception("Call to enum_processes failed")

        num_values = int(bytes_returned.value / ctypes.sizeof(w_windows.wintypes.DWORD))
        for index in range(num_values):
            process_id = process_ids[index]

            h_process = self.open_process(PROCESS_TERMINATE | PROCESS_QUERY_INFORMATION, False, process_id)
            if h_process:
                image_file_name = (ctypes.c_char*MAX_PATH)()
                if self.get_process_image_filename(h_process, image_file_name, MAX_PATH) > 0:
                    filename = os.path.basename(image_file_name.value)
                    if filename == process_name_in_bytes:
                        pid = process_id
                self.close_handle(h_process)
        return pid

    def get_window_rect(self) -> typing.Any:
        rect = w_windows.wintypes.RECT()
        w_windows.windll.user32.GetWindowRect(w_windows.windll.user32.GetForegroundWindow(), ctypes.byref(rect))
        return rect

    def get_process_handle(self, pid: int) -> int:
        return int(self.open_process(0x0510, False, pid))

    def press_key(self, hex_key_code: int) -> None:
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.ki = KeyBdInput( 0, hex_key_code, 0x0008, 0, ctypes.pointer(extra) )
        x = Input( ctypes.c_ulong(1), ii_ )
        w_windows.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    def release_key(self, hex_key_code: int) -> None:
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.ki = KeyBdInput( 0, hex_key_code, 0x0008 | 0x0002, 0, ctypes.pointer(extra) )
        x = Input( ctypes.c_ulong(1), ii_ )
        w_windows.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    def sleep(self, seconds: float) -> None:
        # SetWaitableTimer not working :(
        self.dumb_sleep(seconds)
        # # https://stackoverflow.com/a/11658115
        # # The kernel measures in 100 nanosecond intervals, so we must multiply .25 by 10000
        # delay = ctypes.c_longlong(int(seconds * 10000))
        # self.k32.SetWaitableTimer(self.timer(), ctypes.byref(delay), 0, ctypes.c_void_p(), ctypes.c_void_p(), False)
        # self.k32.WaitForSingleObject(self.timer(), 0xffffffff)

    @staticmethod
    def dumb_sleep(seconds: float) -> None:
        before = time.time()
        buffer_s = 0.0015
        acceptable_early = 0.0005
        smaller_sleep = seconds - buffer_s
        if smaller_sleep > 0:
            time.sleep(smaller_sleep)
        for _ in range(1000000):
            early = seconds - (time.time() - before)
            if early < acceptable_early:
                return

    timer_ = None
    def timer(self) -> typing.Any:
        if self.timer_ == None:
            # This sets the priority of the process to realtime--the same priority as the mouse pointer.
            self.k32.SetThreadPriority(self.k32.GetCurrentThread(), 31)
            # This creates a timer. This only needs to be done once.
            self.timer_ = self.k32.CreateWaitableTimerA(ctypes.c_void_p(), True, ctypes.c_void_p())
        return self.timer_

# C struct redefinitions
PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time",ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                 ("mi", MouseInput),
                 ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]


w = Windows()
