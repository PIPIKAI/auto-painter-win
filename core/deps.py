import sys
from typing import Tuple


def check_runtime_deps() -> Tuple[bool, str]:
    """
    Verify required runtime deps are importable and provide a helpful error message.
    """
    try:
        import numpy  # noqa: F401
    except Exception as exc:
        return (
            False,
            "Missing dependency: numpy.\n"
            "Fix: pip install numpy\n"
            f"Details: {exc}",
        )

    try:
        import cv2  # noqa: F401
        return True, ""
    except Exception:
        # OpenCV optional: allow fallback if Pillow is available
        try:
            from PIL import Image  # noqa: F401
            return True, ""
        except Exception as exc:
            pyver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            return (
                False,
                "OpenCV not available, and Pillow is missing.\n"
                "Fix: pip install -r requirements.txt\n"
                f"Python: {pyver}\n"
                f"Details: {exc}",
            )
    return True, ""
