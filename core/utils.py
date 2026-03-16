import os
import numpy as np

from core.image_ops import decode_image_bytes, resize_image

try:
    import cv2 as _cv2  # type: ignore
except Exception:
    _cv2 = None

_IMREAD_COLOR = _cv2.IMREAD_COLOR if _cv2 is not None else 1
_IMREAD_GRAYSCALE = _cv2.IMREAD_GRAYSCALE if _cv2 is not None else 0

def imread_unicode(path: str, flags=_IMREAD_COLOR):
    """
    可靠读取含中文/特殊字符路径的图片。
    统一返回 RGB（彩色）或灰度（单通道）。
    """
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return None
    grayscale = flags == _IMREAD_GRAYSCALE or flags == 0
    img = decode_image_bytes(data, grayscale=grayscale)
    if img is None:
        return None
    if grayscale:
        return img
    return img  # RGB

def imwrite_unicode(path, img, params=None):
    """
    支持中文路径的 imwrite

    :param path: 保存路径 (支持中文)
    :param img: numpy 图像
    :param params: 编码参数 (和 cv2.imwrite 一样)
    :return: True/False
    """
    try:
        ext = os.path.splitext(path)[1]
        if ext == "":
            raise ValueError("文件必须包含扩展名")

        if _cv2 is not None:
            out = img
            if img.ndim == 3:
                # RGB -> BGR for OpenCV
                out = img[:, :, ::-1]
            if params is None:
                result, buf = _cv2.imencode(ext, out)
            else:
                result, buf = _cv2.imencode(ext, out, params)
            if result:
                buf.tofile(path)
                return True
            return False

        from PIL import Image  # type: ignore

        mode = "L" if img.ndim == 2 else "RGB"
        Image.fromarray(img, mode=mode).save(path)
        return True

    except Exception as e:
        print("imwrite_unicode error:", e)
        return False
    
def map_point(x, y, img_w, img_h, canvas_left, canvas_top, canvas_w, canvas_h, padding=2):
    sx = canvas_left + padding + (x / (img_w - 1)) * (canvas_w - 2 * padding)
    sy = canvas_top + padding + (y / (img_h - 1)) * (canvas_h - 2 * padding)
    return int(sx), int(sy)

def map_point_aspect(x, y, img_w, img_h, draw_left, draw_top, draw_w, draw_h):
    sx = draw_left + (x / (img_w - 1)) * (draw_w - 1)
    sy = draw_top + (y / (img_h - 1)) * (draw_h - 1)
    return int(round(sx)), int(round(sy))

def compute_aspect_fit_rect(img_w, img_h, canvas_left, canvas_top, canvas_w, canvas_h, padding=2):
    """
    在 canvas_rect 内部，计算一个保持 img 宽高比的“内接矩形”，并居中放置。
    返回：draw_left, draw_top, draw_w, draw_h
    """
    # 可用区域（扣掉 padding）
    avail_w = max(1, canvas_w - 2 * padding)
    avail_h = max(1, canvas_h - 2 * padding)

    img_aspect = img_w / img_h
    canvas_aspect = avail_w / avail_h

    if canvas_aspect >= img_aspect:
        # 画布更宽：高度撑满，宽度按比例
        draw_h = avail_h
        draw_w = int(round(draw_h * img_aspect))
    else:
        # 画布更高：宽度撑满，高度按比例
        draw_w = avail_w
        draw_h = int(round(draw_w / img_aspect))

    draw_left = canvas_left + padding + (avail_w - draw_w) // 2
    draw_top = canvas_top + padding + (avail_h - draw_h) // 2

    return draw_left, draw_top, draw_w, draw_h




    # 轮廓很多时，排序一下：从长到短画（减少碎线影响）
    paths.sort(key=lambda p: -len(p))
    return paths

def resize_to_max_side(img_bgr, target_max_side=900, min_side=400):
    h, w = img_bgr.shape[:2]
    max_side = max(w, h)
    min_s = min(w, h)

    # 如果太小就放大（可选：放大太多会糊，但对线稿提取有时反而更稳）
    if max_side < target_max_side:
        scale_up = target_max_side / max_side
    else:
        scale_up = 1.0

    # 如果最短边太小，也确保放到 min_side（避免极窄图）
    if min_s * scale_up < min_side:
        scale_up = min_side / min_s

    # 如果太大就缩小到 target_max_side
    if max_side * scale_up > target_max_side:
        scale = target_max_side / max_side
    else:
        scale = scale_up

    if abs(scale - 1.0) < 1e-6:
        return img_bgr, 1.0

    new_w = int(round(w * scale))
    new_h = int(round(h * scale))
    resized = resize_image(img_bgr, new_w, new_h)
    return resized, scale
