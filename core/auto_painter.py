import time
from dataclasses import dataclass
from typing import Callable, Iterable, Optional

import cv2
import numpy as np
import keyboard
import pyautogui

from core.mouseapi import move_abs, button_down, button_up
from core.utils import compute_aspect_fit_rect, map_point_aspect, imread_unicode


@dataclass
class PainterConfig:
    """
    自动绘画配置，可从界面参数构造。
    """

    draw_button: str = "right"
    draw_speed_sec: float = 0.0025
    start_delay_sec: float = 0.0
    canvas_scale: float = 1.0
    min_contour_len: int = 2
    join_dist_px: int = 5
    allow_bridge_line: bool = True
    bridge_max_dist_px: int = 15
    simplify_eps: float = 0.5
    point_stride: int = 1
    calibrate_start_key: str = "f7"
    calibrate_end_key: str = "f8"
    abort_key: str = "esc"

    @staticmethod
    def _speed_to_delay(speed_value: int) -> float:
        """
        将界面 1-100 的速度值映射到每个点的停顿时间（秒）。
        数值越大越快（约 0.008s → 0.0008s）。
        """
        speed_value = max(1, min(100, int(speed_value)))
        slowest = 0.008
        fastest = 0.0008
        ratio = (speed_value - 1) / 99
        return slowest - (slowest - fastest) * ratio

    @classmethod
    def from_params(cls, params: Optional[dict] = None) -> "PainterConfig":
        params = params or {}
        draw_button = str(params.get("draw_button", cls.draw_button)).lower()
        if draw_button not in {"left", "right"}:
            draw_button = cls.draw_button
        return cls(
            draw_button=draw_button,
            draw_speed_sec=cls._speed_to_delay(params.get("speed", DEFAULT_SPEED_VALUE)),
            # 允许 0 表示立即开始，由 _sleep_with_cancel 内部短路处理
            start_delay_sec=max(0.0, float(params.get("delay", 0))),
            canvas_scale=max(0.1, min(2.0, float(params.get("scale", 1.0)))),
            calibrate_start_key=str(params.get("calibrate_start_key", cls.calibrate_start_key)).lower(),
            calibrate_end_key=str(params.get("calibrate_end_key", cls.calibrate_end_key)).lower(),
            abort_key=str(params.get("abort_key", cls.abort_key)).lower(),
        )


class PaintCancelled(Exception):
    """在绘画过程中用户主动取消。"""


SCALE_EPSILON = 1e-6
CANCEL_CHECK_INTERVAL = 0.1
DEFAULT_SPEED_VALUE = 50


def sketch_to_contours(sketch_u8, config: PainterConfig):
    # 找白色线条的轮廓：需要白为前景
    _, bin_img = cv2.threshold(sketch_u8, 127, 255, cv2.THRESH_BINARY)

    contours, _hier = cv2.findContours(bin_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    paths = []
    for cnt in contours:
        if len(cnt) < config.min_contour_len:
            continue

        # Douglas-Peucker 简化
        approx = cv2.approxPolyDP(cnt, epsilon=config.simplify_eps, closed=False)

        pts = approx.reshape(-1, 2)
        if len(pts) < 2:
            continue

        # 抽样减少点数
        pts2 = pts[:: config.point_stride] if config.point_stride > 1 else pts
        if len(pts2) < 2:
            continue

        paths.append(pts2)
    # 轮廓很多时，排序一下：从长到短画（减少碎线影响）
    paths.sort(key=lambda p: -len(p))
    return paths


def _dist2(a, b):
    dx = float(a[0] - b[0])
    dy = float(a[1] - b[1])
    return dx * dx + dy * dy


def _scale_and_center_draw_rect(draw_rect, canvas_rect, scale: float):
    if abs(scale - 1.0) < SCALE_EPSILON:
        return draw_rect

    draw_left, draw_top, draw_w, draw_h = draw_rect
    canvas_left, canvas_top, canvas_w, canvas_h = canvas_rect

    max_scale = min(
        canvas_w / max(1, draw_w),
        canvas_h / max(1, draw_h),
    )
    scale = min(scale, max_scale)

    scaled_w = max(1, int(round(draw_w * scale)))
    scaled_h = max(1, int(round(draw_h * scale)))
    left = canvas_left + (canvas_w - scaled_w) // 2
    top = canvas_top + (canvas_h - scaled_h) // 2
    return left, top, scaled_w, scaled_h


def calibrate_canvas_rect(
    config: PainterConfig,
    stop_checker: Callable[[], bool],
    status_callback: Optional[Callable[[str], None]] = None,
):
    """
    通过热键让用户用鼠标指向画布左上、右下。
    """
    print("\n== 画布校准 ==")
    print(
        f"把鼠标移动到【画布左上角】按 {config.calibrate_start_key.upper()}；"
        f"移动到【画布右下角】按 {config.calibrate_end_key.upper()}。按 {config.abort_key.upper()} 终止。"
    )
    if status_callback:
        status_callback(
            f"请移动鼠标到画布左上角后按 {config.calibrate_start_key.upper()} 记录"
        )

    p1 = None
    p2 = None

    while p1 is None:
        if stop_checker():
            raise PaintCancelled("cancelled")
        if keyboard.is_pressed(config.calibrate_start_key):
            p1 = pyautogui.position()
            print(f"已记录左上角: {p1}")
            if status_callback:
                status_callback(f"已记录左上角: ({p1.x}, {p1.y})")
            time.sleep(0.3)

    while p2 is None:
        if stop_checker():
            raise PaintCancelled("cancelled")
        if keyboard.is_pressed(config.calibrate_end_key):
            p2 = pyautogui.position()
            print(f"已记录右下角: {p2}")
            if status_callback:
                status_callback(f"已记录右下角: ({p2.x}, {p2.y})")
            time.sleep(0.3)

    left = min(p1.x, p2.x)
    top = min(p1.y, p2.y)
    right = max(p1.x, p2.x)
    bottom = max(p1.y, p2.y)

    width = right - left
    height = bottom - top

    if width < 50 or height < 50:
        raise ValueError("画布区域太小，可能没选对。请重试。")

    return left, top, width, height


def draw_strokes_in_paint(
    strokes: Iterable[np.ndarray],
    img_w: int,
    img_h: int,
    canvas_rect,
    config: PainterConfig,
    progress_callback: Optional[Callable[[int], None]],
    stop_checker: Callable[[], bool],
):
    canvas_left, canvas_top, canvas_w, canvas_h = canvas_rect

    # ✅ 计算等比绘制区域（在用户框选区域内部居中、保持比例）
    draw_rect = compute_aspect_fit_rect(
        img_w, img_h, canvas_left, canvas_top, canvas_w, canvas_h, padding=2
    )
    draw_left, draw_top, draw_w, draw_h = _scale_and_center_draw_rect(
        draw_rect, canvas_rect, config.canvas_scale
    )
    print(f"等比绘制区域：left={draw_left} top={draw_top} w={draw_w} h={draw_h}")

    print("\n== 开始绘画 ==")
    print("请确认：画图窗口已在前台，并选择了【铅笔】工具。")
    print(f"开始后鼠标会被接管；按 {config.abort_key.upper()} 紧急停止。\n")

    pyautogui.PAUSE = 0
    pyautogui.FAILSAFE = True

    total = len(strokes)
    for i, pts in enumerate(strokes, 1):
        if stop_checker():
            raise PaintCancelled("cancelled")

        # 起点移动（用原生 move）
        x0, y0 = pts[0]
        sx0, sy0 = map_point_aspect(x0, y0, img_w, img_h, draw_left, draw_top, draw_w, draw_h)
        move_abs(sx0, sy0)

        button_down(config.draw_button)

        for (x, y) in pts[1:]:
            if stop_checker():
                button_up(config.draw_button)
                raise PaintCancelled("cancelled")

            sx, sy = map_point_aspect(x, y, img_w, img_h, draw_left, draw_top, draw_w, draw_h)
            move_abs(sx, sy)

            time.sleep(config.draw_speed_sec)

        button_up(config.draw_button)

        if i % 10 == 0 or i == total:
            print(f"进度：{i}/{total} 笔")

        progress = int(i / total * 100)
        if progress_callback:
            progress_callback(progress)

    print("\n完成。")


def reorder_and_merge_paths(
    paths,
    join_dist_px=6,
    allow_bridge_line=True,
    bridge_max_dist_px=20,
):
    """
    输入: paths: List[np.ndarray shape=(N,2)]，坐标在“原图像素坐标系”
    输出: strokes: List[np.ndarray]（已合并成更长的点序列）
    """
    if not paths:
        return []

    remaining = [p.copy() for p in paths if len(p) >= 2]
    strokes = []

    # 从最长的开始（也可以从任意开始）
    remaining.sort(key=lambda p: -len(p))

    current_stroke = remaining.pop(0)
    strokes.append(current_stroke)

    while remaining:
        cur_end = strokes[-1][-1]  # 当前笔尖（原图坐标）

        # 找到与 cur_end 最近的 path（比较它的起点和终点）
        best_i = None
        best_reverse = False
        best_d2 = None

        for i, p in enumerate(remaining):
            p0 = p[0]
            p1 = p[-1]

            d2_start = _dist2(cur_end, p0)
            d2_end = _dist2(cur_end, p1)

            if best_d2 is None or d2_start < best_d2 or d2_end < best_d2:
                if d2_start <= d2_end:
                    best_d2 = d2_start
                    best_i = i
                    best_reverse = False
                else:
                    best_d2 = d2_end
                    best_i = i
                    best_reverse = True

        next_path = remaining.pop(best_i)
        if best_reverse:
            next_path = next_path[::-1]

        join2 = float(join_dist_px * join_dist_px)
        bridge2 = float(bridge_max_dist_px * bridge_max_dist_px)

        if best_d2 <= join2:
            # 足够近：直接不断笔拼接（避免重复点）
            strokes[-1] = np.vstack([strokes[-1], next_path[1:]])
        elif allow_bridge_line and best_d2 <= bridge2:
            # 不够近但允许桥接：在两端之间插入一个直线连接（会产生额外连线）
            strokes[-1] = np.vstack([strokes[-1], next_path])
        else:
            # 太远：新开一笔
            strokes.append(next_path)

    return strokes


class AutoPainter:
    """
    自动绘画器：从线稿提取路径，并按配置绘制到指定画布。
    """

    def __init__(
        self,
        sketch_img_path: str,
        config: Optional[PainterConfig] = None,
        stop_checker: Optional[Callable[[], bool]] = None,
    ):
        self.sketch_img_path = sketch_img_path
        self.config = config or PainterConfig()
        self._stop_requested = False
        self._external_stop = stop_checker

    def request_stop(self):
        self._stop_requested = True

    def _should_stop(self) -> bool:
        external = self._external_stop() if self._external_stop else False
        abort_hotkey = keyboard.is_pressed(self.config.abort_key)
        return self._stop_requested or external or abort_hotkey

    def _sleep_with_cancel(self, seconds: float):
        if seconds <= 0:
            return
        end_at = time.time() + seconds
        while time.time() < end_at:
            if self._should_stop():
                raise PaintCancelled("cancelled")
            remaining = end_at - time.time()
            time.sleep(min(CANCEL_CHECK_INTERVAL, max(0.0, remaining)))

    def start(
        self,
        progress_callback: Optional[Callable[[int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
    ):
        cb = progress_callback or (lambda _: None)
        cb(0)

        if self.config.start_delay_sec:
            print(f"开始前等待 {self.config.start_delay_sec:.1f} 秒，便于切换到目标画布...")
            self._sleep_with_cancel(self.config.start_delay_sec)

        sketch = imread_unicode(self.sketch_img_path, 0)
        if sketch is None:
            raise ValueError("无法读取线稿文件，请确认路径有效。")

        # OpenCV shape -> (height, width)
        height = sketch.shape[0]
        width = sketch.shape[1]

        paths = sketch_to_contours(sketch, self.config)
        print(f"提取到路径数：{len(paths)}（越多绘制越慢）")

        strokes = reorder_and_merge_paths(
            paths,
            join_dist_px=self.config.join_dist_px,
            allow_bridge_line=self.config.allow_bridge_line,
            bridge_max_dist_px=self.config.bridge_max_dist_px,
        )
        print(f"合并后笔画数：{len(strokes)}（越少抬笔越少）")

        if not strokes:
            raise ValueError("未找到可绘制的路径，请检查线稿结果。")

        canvas_rect = calibrate_canvas_rect(self.config, self._should_stop, status_callback)
        print(
            f"画布区域：left={canvas_rect[0]} top={canvas_rect[1]} "
            f"w={canvas_rect[2]} h={canvas_rect[3]}"
        )

        draw_strokes_in_paint(
            strokes,
            width,
            height,
            canvas_rect,
            self.config,
            cb,
            self._should_stop,
        )
        cb(100)


def auto_painter_start(sketch_img_path, params, progress_callback, stop_checker=None):
    """
    兼容旧调用方式的启动函数。
    """
    painter = AutoPainter(
        sketch_img_path,
        PainterConfig.from_params(params),
        stop_checker=stop_checker,
    )
    painter.start(progress_callback)
