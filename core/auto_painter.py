import time
import math
import subprocess
import tkinter as tk
from tkinter import filedialog

import cv2
import numpy as np

import pyautogui
import keyboard
from core.mouseapi import move_abs, button_down, button_up
from core.utils import compute_aspect_fit_rect, map_point_aspect, imread_unicode





DRAW_BUTTON = "right"
DRAW_SPEED_SEC = 0.0025
MIN_CONTOUR_LEN = 2          # 过滤很短的轮廓（噪声）
JOIN_DIST_PX = 5          # 在“原图坐标系”里，两段之间小于这个距离就不断笔连接
ALLOW_BRIDGE_LINE = True  # 距离略大也不断笔，用直线桥接（可能产生不想要的连线）
BRIDGE_MAX_DIST_PX = 15   # 允许桥接的最大距离（原图坐标）
SIMPLIFY_EPS = 0.5            # 轮廓简化强度（越大点越少，线越“直”）
POINT_STRIDE = 1              # 路径点抽样：每隔 N 个点取 1 个（越大越快但更粗糙）

def sketch_to_contours(sketch_u8):
    # 找白色线条的轮廓：需要白为前景
    _, bin_img = cv2.threshold(sketch_u8, 127, 255, cv2.THRESH_BINARY)

    # contours, _hier = cv2.findContours(bin_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours, _hier = cv2.findContours(bin_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    paths = []
    for cnt in contours:
        if len(cnt) < MIN_CONTOUR_LEN:
            continue

        # Douglas-Peucker 简化
        eps = SIMPLIFY_EPS
        approx = cv2.approxPolyDP(cnt, epsilon=eps, closed=False)

        pts = approx.reshape(-1, 2)
        if len(pts) < 2:
            continue

        # 抽样减少点数
        pts2 = pts[::POINT_STRIDE] if POINT_STRIDE > 1 else pts
        if len(pts2) < 2:
            continue

        paths.append(pts2)
    # 轮廓很多时，排序一下：从长到短画（减少碎线影响）
    paths.sort(key=lambda p: -len(p))
    return paths

def _dist2(a, b):
    dx = float(a[0] - b[0])
    dy = float(a[1] - b[1])
    return dx*dx + dy*dy

def calibrate_canvas_rect():
    """
    通过热键让用户用鼠标指向画布左上、右下
    """
    print("\n== 画布校准 ==")
    print("把鼠标移动到【画布左上角】然后按 F8；再移动到【画布右下角】按 F9。按 ESC 终止。")

    p1 = None
    p2 = None

    while p1 is None:
        if keyboard.is_pressed("esc"):
            raise SystemExit("用户终止")
        if keyboard.is_pressed("f8"):
            p1 = pyautogui.position()
            print(f"已记录左上角: {p1}")
            time.sleep(0.3)

    while p2 is None:
        if keyboard.is_pressed("esc"):
            raise SystemExit("用户终止")
        if keyboard.is_pressed("f9"):
            p2 = pyautogui.position()
            print(f"已记录右下角: {p2}")
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

def draw_strokes_in_paint(strokes, img_w, img_h, canvas_rect, progress_callback):
    canvas_left, canvas_top, canvas_w, canvas_h = canvas_rect

    # ✅ 计算等比绘制区域（在用户框选区域内部居中、保持比例）
    draw_left, draw_top, draw_w, draw_h = compute_aspect_fit_rect(
        img_w, img_h, canvas_left, canvas_top, canvas_w, canvas_h, padding=2
    )
    print(f"等比绘制区域：left={draw_left} top={draw_top} w={draw_w} h={draw_h}")

    print("\n== 开始绘画 ==")
    print("请确认：画图窗口已在前台，并选择了【铅笔】工具。")
    print("开始后鼠标会被接管；按 ESC 紧急停止。\n")
    time.sleep(1.0)

    pyautogui.PAUSE = 0
    pyautogui.FAILSAFE = True

    total = len(strokes)
    for i, pts in enumerate(strokes, 1):
        if keyboard.is_pressed("esc"):
            raise SystemExit("用户终止")

        # 起点移动（用原生 move）
        x0, y0 = pts[0]
        sx0, sy0 = map_point_aspect(x0, y0, img_w, img_h, draw_left, draw_top, draw_w, draw_h)
        move_abs(sx0, sy0)

        button_down(DRAW_BUTTON)

        for (x, y) in pts[1:]:
            if keyboard.is_pressed("esc"):
                button_up(DRAW_BUTTON)
                raise SystemExit("用户终止")

            sx, sy = map_point_aspect(x, y, img_w, img_h, draw_left, draw_top, draw_w, draw_h)
            move_abs(sx, sy)

            time.sleep(DRAW_SPEED_SEC)

        button_up(DRAW_BUTTON)

        if i % 10 == 0 or i == total:
            print(f"进度：{i}/{total} 笔")
        
        progress = int(i/total * 100)
        print(f"progress: {progress}")
        progress_callback(progress)
            

    print("\n完成。")


def reorder_and_merge_paths(paths, join_dist_px=6, allow_bridge_line=True, bridge_max_dist_px=20):
    """
    输入: paths: List[np.ndarray shape=(N,2)]，坐标在“原图像素坐标系”
    输出: strokes: List[List[np.ndarray]] 或更简单：List[np.ndarray]（已合并成更长的点序列）

    这里直接输出 strokes: List[np.ndarray]，每个 stroke 是一笔连续的点序列。
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


def auto_painter_start(sketch_img_path, parms , progress_callback):

    sketch = imread_unicode(sketch_img_path, 0)
    w,h = sketch.shape[:2]
    paths = sketch_to_contours(sketch)
    print(f"提取到路径数：{len(paths)}（越多绘制越慢）")


    strokes = reorder_and_merge_paths(
        paths,
        join_dist_px=JOIN_DIST_PX,
        allow_bridge_line=ALLOW_BRIDGE_LINE,
        bridge_max_dist_px=BRIDGE_MAX_DIST_PX,
    )
    print(f"合并后笔画数：{len(strokes)}（越少抬笔越少）")

    canvas_rect = calibrate_canvas_rect()
    print(f"画布区域：left={canvas_rect[0]} top={canvas_rect[1]} w={canvas_rect[2]} h={canvas_rect[3]}")

    draw_strokes_in_paint(strokes, w, h, canvas_rect , progress_callback)
