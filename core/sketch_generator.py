import os
from typing import Dict, Optional, Tuple

import numpy as np

from core import image_ops
from core.utils import imread_unicode, resize_to_max_side, imwrite_unicode


class SketchGenerator:
    """
    线稿生成器（面向 UI 的类封装）

    参数映射：
    - thickness: 线条粗细（1-10）
    - contrast : 对比度（0-100，50 为原图对比度）
    - threshold: 阈值（0-255，影响边缘强度/色块数量）
    - invert   : 是否反色
    """

    DEFAULT_PARAMS = {
        "thickness": 3,
        "contrast": 50,
        "threshold": 127,
        "invert": False,
    }

    def __init__(self, target_max_side: int = 900, min_side: int = 400):
        self.target_max_side = target_max_side
        self.min_side = min_side

    # ----------------------------
    # Public API
    # ----------------------------
    def generate(self, img_path: str, style: str, params: Optional[dict] = None) -> str:
        """生成线稿并返回预览文件路径。"""
        img_rgb = imread_unicode(img_path)
        if img_rgb is None:
            raise RuntimeError("图片读取失败，请换一张或检查路径。")

        normalized_params = self._normalize_params(params or {})
        img_rgb, scale = resize_to_max_side(
            img_rgb, target_max_side=self.target_max_side, min_side=self.min_side
        )
        print(f"图片已缩放，scale={scale:.3f}，新尺寸={img_rgb.shape[1]}x{img_rgb.shape[0]}")

        sketch = self._render_by_style(img_rgb, style, normalized_params)

        if normalized_params["invert"]:
            sketch = 255 - sketch

        out_dir = os.path.join(os.path.dirname(img_path), "out_sketch")
        os.makedirs(out_dir, exist_ok=True)
        preview_path = os.path.join(out_dir, "sketch.png")
        imwrite_unicode(preview_path, sketch)
        print(f"线稿预览已保存：{preview_path}")

        return preview_path

    # ----------------------------
    # Style dispatch
    # ----------------------------
    def _render_by_style(
        self, img_rgb: np.ndarray, style: str, params: Dict[str, object]
    ) -> np.ndarray:
        style_key = (style or "").lower()
        handlers = {
            # UI 样式
            "pencil": self._style_pencil,
            "pen": self._style_pen,
            "ink": self._style_ink,
            "comic": self._style_comic,
            "contour": self._style_contour,
            "ai": self._style_pen,  # 临时复用钢笔风格
            # 兼容旧值
            "sketch_mono": self._style_ink,
            "flat_poster": self._style_comic,
            "edges": self._style_contour,
        }

        handler = handlers.get(style_key)
        if handler is None:
            raise ValueError(f"Unknown STYLE: {style}")

        return handler(img_rgb, params)

    # ----------------------------
    # Individual styles
    # ----------------------------
    def _style_pencil(self, img_rgb: np.ndarray, params: Dict[str, object]) -> np.ndarray:
        """柔和铅笔风格：平滑 + Canny 边缘 + 可调粗细"""
        gray = image_ops.to_gray(img_rgb)
        gray = image_ops.gaussian_blur(gray, ksize=5, sigma=0)
        gray = image_ops.scale_abs(gray, alpha=self._contrast_alpha(params), beta=0)

        low, high = self._canny_thresholds(params)
        edges = image_ops.canny(gray, low, high)
        return self._thicken(edges, params)

    def _style_pen(self, img_rgb: np.ndarray, params: Dict[str, object]) -> np.ndarray:
        """钢笔风格：边缘 + 闭运算让线条更连贯"""
        edges = self._style_pencil(img_rgb, params)
        kernel = self._kernel(max(1, params["thickness"] // 2 + 1))
        edges = image_ops.morph_close(edges, kernel.shape[0])
        return edges

    def _style_ink(self, img_rgb: np.ndarray, params: Dict[str, object]) -> np.ndarray:
        """水墨/素描：双边滤波 + 全局阈值"""
        gray = image_ops.to_gray(img_rgb)
        gray = image_ops.bilateral_filter(gray, d=7, sigma_color=60, sigma_space=60)
        gray = image_ops.scale_abs(gray, alpha=self._contrast_alpha(params), beta=0)

        bw = image_ops.threshold_binary(gray, params["threshold"], invert=True)
        bw = self._thicken(bw, params)
        return bw

    def _style_comic(self, img_rgb: np.ndarray, params: Dict[str, object]) -> np.ndarray:
        """漫画/平涂：颜色量化 + 边缘提取"""
        smooth = image_ops.bilateral_filter(
            img_rgb, d=7 + params["thickness"], sigma_color=80, sigma_space=80
        )
        if smooth.ndim == 2:
            smooth_rgb = np.stack([smooth, smooth, smooth], axis=2)
        else:
            smooth_rgb = smooth
        quant = image_ops.quantize_colors(smooth_rgb, self._color_bins(params))

        qgray = image_ops.to_gray(quant)
        qgray = image_ops.gaussian_blur(qgray, ksize=3, sigma=0)

        edges = image_ops.canny(qgray, 40, 120)
        edges = self._thicken(edges, params)
        return edges

    def _style_contour(self, img_rgb: np.ndarray, params: Dict[str, object]) -> np.ndarray:
        """轮廓提取：轻微平滑 + 边缘"""
        gray = image_ops.to_gray(img_rgb)
        gray = image_ops.gaussian_blur(gray, ksize=3, sigma=0)
        gray = image_ops.scale_abs(gray, alpha=self._contrast_alpha(params), beta=0)

        low, high = self._canny_thresholds(params, contour_mode=True)
        edges = image_ops.canny(gray, low, high)
        edges = self._thicken(edges, params)
        return edges

    # ----------------------------
    # Helpers
    # ----------------------------
    def _normalize_params(self, params: dict) -> Dict[str, object]:
        merged = {**self.DEFAULT_PARAMS}
        for key, default_val in self.DEFAULT_PARAMS.items():
            if key in params:
                merged[key] = params.get(key, default_val)

        merged["thickness"] = max(1, int(round(float(merged["thickness"]))))
        merged["contrast"] = max(0.1, float(merged["contrast"]))
        merged["threshold"] = int(np.clip(int(merged["threshold"]), 0, 255))
        merged["invert"] = bool(merged["invert"])
        return merged

    def _contrast_alpha(self, params: Dict[str, object]) -> float:
        # 滑块 50 -> 1.0，100 -> 2.0
        return max(0.1, params["contrast"] / 50.0)

    def _canny_thresholds(
        self, params: Dict[str, object], contour_mode: bool = False
    ) -> Tuple[int, int]:
        high = int(np.clip(params["threshold"], 30, 255))
        ratio = 0.4 if contour_mode else 0.5
        low = max(5, int(high * ratio))
        return low, high

    def _kernel(self, thickness: int) -> np.ndarray:
        size = max(1, int(thickness))
        if size % 2 == 0:
            size += 1
        return np.ones((size, size), np.uint8)

    def _thicken(self, img: np.ndarray, params: dict) -> np.ndarray:
        if params["thickness"] <= 1:
            return img
        k = self._kernel(params["thickness"]).shape[0]
        return image_ops.dilate(img, k)

    def _color_bins(self, params: dict) -> int:
        """根据阈值动态调整分块色数，阈值越小色块越少"""
        return max(2, min(12, int(2 + (params["threshold"] / 255.0) * 10)))


def generate_sketch(img_path, style, params):
    """兼容旧调用方式的便捷函数"""
    generator = SketchGenerator()
    return generator.generate(img_path, style, params)
