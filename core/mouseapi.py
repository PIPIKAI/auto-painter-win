
import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

# ✅ 兼容：wintypes 可能没有 ULONG_PTR（你现在就遇到了）
ULONG_PTR = ctypes.c_uint64 if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_uint32

INPUT_MOUSE = 0

MOUSEEVENTF_MOVE        = 0x0001
MOUSEEVENTF_LEFTDOWN    = 0x0002
MOUSEEVENTF_LEFTUP      = 0x0004
MOUSEEVENTF_RIGHTDOWN   = 0x0008
MOUSEEVENTF_RIGHTUP     = 0x0010
MOUSEEVENTF_ABSOLUTE    = 0x8000

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),  # ✅ 改这里
    ]

class INPUT(ctypes.Structure):
    class _I(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("i",)
    _fields_ = [("type", wintypes.DWORD), ("i", _I)]

def _send(flags: int, x: int | None = None, y: int | None = None):
    mi = MOUSEINPUT(0, 0, 0, flags, 0, 0)

    if x is not None and y is not None:
        sw = user32.GetSystemMetrics(0)
        sh = user32.GetSystemMetrics(1)
        mi.dx = int(x * 65535 / (sw - 1))
        mi.dy = int(y * 65535 / (sh - 1))
        mi.dwFlags |= MOUSEEVENTF_ABSOLUTE

    inp = INPUT(type=INPUT_MOUSE, mi=mi)
    n = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    if n != 1:
        raise ctypes.WinError(ctypes.get_last_error())

def move_abs(x: int, y: int):
    _send(MOUSEEVENTF_MOVE, x, y)

def button_down(button: str):
    if button == "left":
        _send(MOUSEEVENTF_LEFTDOWN)
    elif button == "right":
        _send(MOUSEEVENTF_RIGHTDOWN)
    else:
        raise ValueError(f"Unsupported button: {button}")

def button_up(button: str):
    if button == "left":
        _send(MOUSEEVENTF_LEFTUP)
    elif button == "right":
        _send(MOUSEEVENTF_RIGHTUP)
    else:
        raise ValueError(f"Unsupported button: {button}")