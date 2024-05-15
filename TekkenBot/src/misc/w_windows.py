# mypy: disable_error_code="unused-ignore"

import ctypes
import typing

from ctypes import wintypes as _wintypes

wintypes = _wintypes

valid = False
windll: typing.Any
WinDLL: typing.Any
try:
    from ctypes import windll # type: ignore
    WinDLL = ctypes.WinDLL # type: ignore
    valid = True
except ImportError:
    pass
