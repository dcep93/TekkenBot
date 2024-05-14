import typing

valid = False
wintypes: typing.Any
windll: typing.Any
WinDLL: typing.Any
try:
    from ctypes import wintypes
    from ctypes import windll # type: ignore
    valid = True
except ModuleNotFoundError:
    pass
