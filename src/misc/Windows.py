import ctypes
import os.path
import sys
import time

# this is trash and could stand to be rewritten
class Windows:
    valid = True
    def __init__(self):
        try:
            from ctypes import wintypes
        except ValueError:
            self.__class__.valid = False
            return

        self.wintypes = wintypes
        self.k32 = ctypes.windll.kernel32

        self.open_process = self.k32.OpenProcess
        self.open_process.argtypes = [wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD]
        self.open_process.restype = wintypes.HANDLE

        self.read_process_memory = self.k32.ReadProcessMemory
        self.read_process_memory.argtypes = [wintypes.HANDLE, ctypes.wintypes.LPCVOID, ctypes.wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        self.read_process_memory.restype = wintypes.BOOL

        self.get_last_error = self.k32.GetLastError
        self.get_last_error.argtypes = None
        self.get_last_error.restype = wintypes.DWORD

        self.close_handle = self.k32.CloseHandle
        self.close_handle.argtypes = [wintypes.HANDLE]
        self.close_handle.restype = wintypes.BOOL

        psapi = ctypes.WinDLL('Psapi.dll')
        self.enum_processes = psapi.EnumProcesses
        self.enum_processes.restype = wintypes.BOOL
        self.get_process_image_filename = psapi.GetProcessImageFileNameA
        self.get_process_image_filename.restype = wintypes.DWORD

    @staticmethod
    def get_module_address(pid, name):
        class ModuleEntry(ctypes.Structure):
            _fields_ = [('dwSize', w.wintypes.DWORD),
                        ('th32ModuleID', w.wintypes.DWORD),
                        ('th32ProcessID', w.wintypes.DWORD),
                        ('GlblcntUsage', w.wintypes.DWORD),
                        ('ProccntUsage', w.wintypes.DWORD),
                        ('modBaseAddr', ctypes.POINTER(w.wintypes.BYTE)),
                        ('modBaseSize', w.wintypes.DWORD),
                        ('hModule', w.wintypes.HMODULE),
                        ('szModule', ctypes.c_char * 256),
                        ('szExePath', ctypes.c_char * 260)]

        # Establish rights and basic options needed for all process declartion / iteration
        TH32CS_SNAPMODULE = 0x00000008

        me32 = ModuleEntry()
        me32.dwSize = ctypes.sizeof(ModuleEntry)

        h_module_snap = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, pid)
        if h_module_snap == -1:
            print('CreateToolhelp32Snapshot Error [%d]' % w.get_last_error())
            print('Build the code yourself? This is the error for using 32-bit Python. Try the 64-bit version.')

        ret = ctypes.windll.kernel32.Module32First(h_module_snap, ctypes.pointer(me32))
        if ret == 0:
            print('ListProcessModules() Error on Module32First[%d]' % w.get_last_error())
            w.close_handle(h_module_snap)

        address_to_return = None
        while ret:
            if name == me32.szModule.decode("utf-8"):
                address_to_return = me32.hModule

            ret = ctypes.windll.kernel32.Module32Next(h_module_snap, ctypes.pointer(me32))
        w.close_handle(h_module_snap)

        return address_to_return

    @staticmethod
    def get_foreground_pid():
        pid = w.wintypes.DWORD()
        active = ctypes.windll.user32.GetForegroundWindow()
        ctypes.windll.user32.GetWindowThreadProcessId(active, ctypes.byref(pid))
        return pid.value

    @staticmethod
    def get_pid(process_name):
        MAX_PATH = 260
        PROCESS_TERMINATE = 0x0001
        PROCESS_QUERY_INFORMATION = 0x0400

        process_name_in_bytes = str.encode(process_name)
        pid = None
        count = 32
        for _ in range(1000):
            process_ids = (w.wintypes.DWORD*count)()
            cb = ctypes.sizeof(process_ids)
            bytes_returned = w.wintypes.DWORD()
            # ???
            if w.enum_processes(ctypes.byref(process_ids), cb, ctypes.byref(bytes_returned)):
                if bytes_returned.value < cb:
                    break
                count *= 2
            else:
                raise Exception("Call to enum_processes failed")
        print("impossible b")

        num_values = int(bytes_returned.value / ctypes.sizeof(w.wintypes.DWORD))
        for index in range(num_values):
            process_id = process_ids[index]

            h_process = w.open_process(PROCESS_TERMINATE | PROCESS_QUERY_INFORMATION, False, process_id)
            if h_process:
                image_file_name = (ctypes.c_char*MAX_PATH)()
                if w.get_process_image_filename(h_process, image_file_name, MAX_PATH) > 0:
                    filename = os.path.basename(image_file_name.value)
                    if filename == process_name_in_bytes:
                        pid = process_id
                w.close_handle(h_process)
        return pid

    @staticmethod
    def press_key(hex_key_code):
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.ki = KeyBdInput( 0, hex_key_code, 0x0008, 0, ctypes.pointer(extra) )
        x = Input( ctypes.c_ulong(1), ii_ )
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    @staticmethod
    def release_key(hex_key_code):
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.ki = KeyBdInput( 0, hex_key_code, 0x0008 | 0x0002, 0, ctypes.pointer(extra) )
        x = Input( ctypes.c_ulong(1), ii_ )
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    @staticmethod
    def sleep(seconds):
        # SetWaitableTimer not working :(
        w.dumb_sleep(seconds)
        # # https://stackoverflow.com/a/11658115
        # # The kernel measures in 100 nanosecond intervals, so we must multiply .25 by 10000
        # delay = ctypes.c_longlong(int(seconds * 10000))
        # w.k32.SetWaitableTimer(w.timer(), ctypes.byref(delay), 0, ctypes.c_void_p(), ctypes.c_void_p(), False)
        # w.k32.WaitForSingleObject(w.timer(), 0xffffffff)

    @staticmethod
    def dumb_sleep(seconds):
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
    @classmethod
    def timer(cls):
        if cls.timer_ == None:
            # This sets the priority of the process to realtime--the same priority as the mouse pointer.
            w.k32.SetThreadPriority(w.k32.GetCurrentThread(), 31)
            # This creates a timer. This only needs to be done once.
            cls.timer_ = w.k32.CreateWaitableTimerA(ctypes.c_void_p(), True, ctypes.c_void_p())
        return cls.timer_

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
