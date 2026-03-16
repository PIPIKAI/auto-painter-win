import io
from typing import Optional

import numpy as np

try:
    import cv2 as _cv2  # type: ignore
except Exception:
    _cv2 = None


def has_cv2() -> bool:
    return _cv2 is not None


def decode_image_bytes(data: bytes, grayscale: bool = False) -> Optional[np.ndarray]:
    if _cv2 is not None:
        arr = np.frombuffer(data, np.uint8)
        flag = _cv2.IMREAD_GRAYSCALE if grayscale else _cv2.IMREAD_COLOR
        img = _cv2.imdecode(arr, flag)
        if img is None:
            return None
        if not grayscale:
            img = _cv2.cvtColor(img, _cv2.COLOR_BGR2RGB)
        return img

    try:
        from PIL import Image  # type: ignore
    except Exception:
        return None

    img = Image.open(io.BytesIO(data))
    if grayscale:
        return np.array(img.convert("L"))
    return np.array(img.convert("RGB"))


def to_gray(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return img.astype(np.uint8)
    # Assume RGB
    r = img[:, :, 0].astype(np.float32)
    g = img[:, :, 1].astype(np.float32)
    b = img[:, :, 2].astype(np.float32)
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    return np.clip(gray, 0, 255).astype(np.uint8)


def scale_abs(gray: np.ndarray, alpha: float = 1.0, beta: float = 0.0) -> np.ndarray:
    out = gray.astype(np.float32) * float(alpha) + float(beta)
    return np.clip(out, 0, 255).astype(np.uint8)


def gaussian_blur(gray: np.ndarray, ksize: int = 5, sigma: float = 0.0) -> np.ndarray:
    if _cv2 is not None:
        return _cv2.GaussianBlur(gray, (ksize, ksize), sigma)
    return box_blur(gray, ksize)


def bilateral_filter(img: np.ndarray, d: int, sigma_color: float, sigma_space: float) -> np.ndarray:
    if _cv2 is not None:
        return _cv2.bilateralFilter(img, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)
    # Fallback: approximate with Gaussian blur on grayscale
    ksize = max(3, int(d) | 1)
    gray = to_gray(img) if img.ndim == 3 else img
    return gaussian_blur(gray, ksize=ksize, sigma=0.0)


def canny(gray: np.ndarray, low: int, high: int) -> np.ndarray:
    if _cv2 is not None:
        return _cv2.Canny(gray, low, high)

    mag = sobel_magnitude(gray)
    strong = mag >= high
    weak = (mag >= low) & ~strong
    if np.any(strong):
        strong_dilated = dilate(strong.astype(np.uint8) * 255, 3) > 0
        edges = strong | (strong_dilated & weak)
    else:
        edges = strong
    return (edges.astype(np.uint8) * 255)


def threshold_binary(gray: np.ndarray, thresh: int, invert: bool = False) -> np.ndarray:
    if invert:
        return np.where(gray <= thresh, 255, 0).astype(np.uint8)
    return np.where(gray > thresh, 255, 0).astype(np.uint8)


def dilate(img: np.ndarray, ksize: int) -> np.ndarray:
    if _cv2 is not None:
        kernel = np.ones((ksize, ksize), np.uint8)
        return _cv2.dilate(img, kernel, iterations=1)
    return _morph(img, ksize, op="max")


def erode(img: np.ndarray, ksize: int) -> np.ndarray:
    if _cv2 is not None:
        kernel = np.ones((ksize, ksize), np.uint8)
        return _cv2.erode(img, kernel, iterations=1)
    return _morph(img, ksize, op="min")


def morph_close(img: np.ndarray, ksize: int) -> np.ndarray:
    if _cv2 is not None:
        kernel = np.ones((ksize, ksize), np.uint8)
        return _cv2.morphologyEx(img, _cv2.MORPH_CLOSE, kernel)
    return erode(dilate(img, ksize), ksize)


def quantize_colors(img_rgb: np.ndarray, bins: int) -> np.ndarray:
    if _cv2 is not None:
        Z = img_rgb.reshape((-1, 3)).astype(np.float32)
        criteria = (_cv2.TERM_CRITERIA_EPS + _cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        colors = int(max(2, bins))
        _ret, labels, centers = _cv2.kmeans(Z, colors, None, criteria, 3, _cv2.KMEANS_PP_CENTERS)
        centers = centers.astype(np.uint8)
        return centers[labels.flatten()].reshape(img_rgb.shape)

    levels = max(2, int(round(bins ** (1.0 / 3.0))))
    step = 255.0 / max(1, (levels - 1))
    quant = np.round(img_rgb.astype(np.float32) / step) * step
    return np.clip(quant, 0, 255).astype(np.uint8)


def resize_image(img: np.ndarray, new_w: int, new_h: int) -> np.ndarray:
    if _cv2 is not None:
        interp = _cv2.INTER_AREA if new_w * new_h < img.shape[0] * img.shape[1] else _cv2.INTER_CUBIC
        return _cv2.resize(img, (new_w, new_h), interpolation=interp)
    try:
        from PIL import Image  # type: ignore
    except Exception:
        return img
    mode = "L" if img.ndim == 2 else "RGB"
    pil = Image.fromarray(img, mode=mode)
    pil = pil.resize((new_w, new_h), resample=Image.BICUBIC)
    return np.array(pil)


def box_blur(gray: np.ndarray, ksize: int) -> np.ndarray:
    ksize = max(1, int(ksize))
    if ksize == 1:
        return gray
    pad = ksize // 2
    padded = np.pad(gray.astype(np.float32), ((pad, pad), (pad, pad)), mode="edge")
    integral = padded.cumsum(axis=0).cumsum(axis=1)
    h, w = gray.shape
    s = (
        integral[ksize:, ksize:]
        - integral[:-ksize, ksize:]
        - integral[ksize:, :-ksize]
        + integral[:-ksize, :-ksize]
    )
    out = s / float(ksize * ksize)
    return np.clip(out, 0, 255).astype(np.uint8)


def sobel_magnitude(gray: np.ndarray) -> np.ndarray:
    g = gray.astype(np.float32)
    p = np.pad(g, ((1, 1), (1, 1)), mode="edge")
    gx = (
        (p[0:-2, 2:] + 2 * p[1:-1, 2:] + p[2:, 2:])
        - (p[0:-2, 0:-2] + 2 * p[1:-1, 0:-2] + p[2:, 0:-2])
    )
    gy = (
        (p[2:, 0:-2] + 2 * p[2:, 1:-1] + p[2:, 2:])
        - (p[0:-2, 0:-2] + 2 * p[0:-2, 1:-1] + p[0:-2, 2:])
    )
    mag = np.hypot(gx, gy)
    maxv = float(mag.max()) if mag.size else 0.0
    if maxv > 0:
        mag = mag / maxv * 255.0
    return np.clip(mag, 0, 255).astype(np.uint8)


def _morph(img: np.ndarray, ksize: int, op: str) -> np.ndarray:
    ksize = max(1, int(ksize))
    if ksize == 1:
        return img
    pad = ksize // 2
    padded = np.pad(img, ((pad, pad), (pad, pad)), mode="edge")
    h, w = img.shape
    if op == "max":
        out = np.zeros((h, w), dtype=img.dtype)
        for dy in range(ksize):
            for dx in range(ksize):
                out = np.maximum(out, padded[dy:dy + h, dx:dx + w])
        return out
    out = np.full((h, w), 255, dtype=img.dtype)
    for dy in range(ksize):
        for dx in range(ksize):
            out = np.minimum(out, padded[dy:dy + h, dx:dx + w])
    return out
