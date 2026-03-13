import platform
import threading
from typing import Optional

_keyboard = None
if platform.system() == "Windows":
    try:
        import keyboard as _keyboard  # type: ignore
    except Exception:
        _keyboard = None

_mac_key_state = None
if platform.system() == "Darwin":
    try:
        import ctypes
        import ctypes.util

        _cg_path = ctypes.util.find_library("CoreGraphics")
        if _cg_path:
            _cg = ctypes.CDLL(_cg_path)
            _cg.CGEventSourceKeyState.argtypes = [ctypes.c_uint32, ctypes.c_uint16]
            _cg.CGEventSourceKeyState.restype = ctypes.c_bool

            def _mac_key_state(keycode: int) -> bool:
                # kCGEventSourceStateCombinedSessionState = 0
                return bool(_cg.CGEventSourceKeyState(0, ctypes.c_uint16(keycode)))
        else:
            _mac_key_state = None
    except Exception:
        _mac_key_state = None

if _keyboard is None and _mac_key_state is None:
    try:
        from pynput import keyboard as _pynput_keyboard  # type: ignore
    except Exception as exc:  # pragma: no cover - import error handled at runtime
        _pynput_keyboard = None
        _pynput_import_error: Optional[Exception] = exc
    else:
        _pynput_import_error = None

    _pressed_keys = set()
    _listener = None
    _lock = threading.Lock()

    _SPECIAL_KEYS = {}
    if _pynput_keyboard is not None:
        _SPECIAL_KEYS = {
            _pynput_keyboard.Key.esc: "esc",
            _pynput_keyboard.Key.enter: "enter",
            _pynput_keyboard.Key.space: "space",
            _pynput_keyboard.Key.tab: "tab",
            _pynput_keyboard.Key.backspace: "backspace",
            _pynput_keyboard.Key.delete: "delete",
            _pynput_keyboard.Key.shift: "shift",
            _pynput_keyboard.Key.shift_r: "shift",
            _pynput_keyboard.Key.ctrl: "ctrl",
            _pynput_keyboard.Key.ctrl_r: "ctrl",
            _pynput_keyboard.Key.alt: "alt",
            _pynput_keyboard.Key.alt_r: "alt",
            _pynput_keyboard.Key.cmd: "cmd",
            _pynput_keyboard.Key.cmd_r: "cmd",
        }
        for i in range(1, 25):
            key_attr = f"f{i}"
            if hasattr(_pynput_keyboard.Key, key_attr):
                _SPECIAL_KEYS[getattr(_pynput_keyboard.Key, key_attr)] = key_attr


def _normalize_key_name(name: str) -> str:
    norm = name.lower().replace(" ", "")
    if norm in {"escape"}:
        return "esc"
    return norm


def _pynput_key_to_name(key) -> Optional[str]:
    if _pynput_keyboard is None:
        return None
    if isinstance(key, _pynput_keyboard.KeyCode):
        if key.char:
            return _normalize_key_name(key.char)
        return None
    return _SPECIAL_KEYS.get(key)


def _ensure_listener():
    global _listener
    if _listener is not None:
        return
    if _pynput_keyboard is None:
        raise RuntimeError(
            "pynput not available; cannot listen for global hotkeys."
        )

    def _on_press(key):
        name = _pynput_key_to_name(key)
        if not name:
            return
        with _lock:
            _pressed_keys.add(name)

    def _on_release(key):
        name = _pynput_key_to_name(key)
        if not name:
            return
        with _lock:
            _pressed_keys.discard(name)

    _listener = _pynput_keyboard.Listener(
        on_press=_on_press,
        on_release=_on_release,
    )
    _listener.daemon = True
    _listener.start()


def is_pressed(key: str) -> bool:
    """
    Cross-platform key pressed check.
    Windows: uses `keyboard` package.
    macOS/Linux: uses `pynput` global listener.
    """
    norm = _normalize_key_name(key)
    if _keyboard is not None:
        try:
            return _keyboard.is_pressed(norm)
        except Exception:
            return False

    if _mac_key_state is not None:
        keycode = _mac_keycode(norm)
        if keycode is None:
            return False
        try:
            return _mac_key_state(keycode)
        except Exception:
            return False

    if _pynput_keyboard is None:
        if _pynput_import_error:
            raise RuntimeError(
                "pynput is required for hotkeys on this platform."
            ) from _pynput_import_error
        raise RuntimeError("pynput is required for hotkeys on this platform.")

    _ensure_listener()
    with _lock:
        return norm in _pressed_keys


def _mac_keycode(key: str) -> Optional[int]:
    if not key:
        return None
    if key in {"esc", "escape"}:
        return 53
    if key.startswith("f") and key[1:].isdigit():
        fnum = int(key[1:])
        return {
            1: 122, 2: 120, 3: 99, 4: 118, 5: 96, 6: 97,
            7: 98, 8: 100, 9: 101, 10: 109, 11: 103, 12: 111,
        }.get(fnum)
    if key == "space":
        return 49
    if key == "tab":
        return 48
    if key == "enter" or key == "return":
        return 36
    if key == "backspace":
        return 51
    if key == "delete":
        return 51

    # Letters
    letters = {
        "a": 0, "s": 1, "d": 2, "f": 3, "h": 4, "g": 5, "z": 6, "x": 7,
        "c": 8, "v": 9, "b": 11, "q": 12, "w": 13, "e": 14, "r": 15,
        "y": 16, "t": 17, "o": 31, "u": 32, "i": 34, "p": 35, "l": 37,
        "j": 38, "k": 40, "n": 45, "m": 46,
    }
    if key in letters:
        return letters[key]

    # Digits
    digits = {
        "1": 18, "2": 19, "3": 20, "4": 21, "5": 23, "6": 22,
        "7": 26, "8": 28, "9": 25, "0": 29,
    }
    return digits.get(key)
