"""
AI 线稿生成器
通过配置好的 API（OpenAI DALL-E / Stable Diffusion / 自定义接口）生成线稿。
"""
import io
import json
import os
import base64
from typing import Optional
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError

import numpy as np

from core.image_ops import decode_image_bytes, threshold_binary
from core.utils import imwrite_unicode


# ─────────── 预设 Prompt 列表 ───────────

PRESET_PROMPTS = [
    {
        "name_zh": "简洁线稿",
        "name_en": "Clean Line Art",
        "prompt": (
            "Convert this image into a clean black-and-white line drawing. "
            "Use thin, precise outlines with no shading or color fill. "
            "The result should look like a coloring book page."
        ),
    },
    {
        "name_zh": "铅笔素描",
        "name_en": "Pencil Sketch",
        "prompt": (
            "Transform this image into a detailed pencil sketch. "
            "Include cross-hatching for shading and fine pencil strokes for texture. "
            "The output should be black and white on a white background."
        ),
    },
    {
        "name_zh": "漫画风格",
        "name_en": "Comic Style",
        "prompt": (
            "Redraw this image in a manga/comic line art style. "
            "Use bold outlines for the main shapes, thinner lines for details, "
            "and screen-tone style dot shading for depth. Black and white only."
        ),
    },
    {
        "name_zh": "建筑线稿",
        "name_en": "Architectural Sketch",
        "prompt": (
            "Convert this image into an architectural line drawing. "
            "Use straight, confident lines with perspective accuracy. "
            "Include construction lines and annotations style. Black on white."
        ),
    },
    {
        "name_zh": "水墨画",
        "name_en": "Ink Wash Painting",
        "prompt": (
            "Transform this image into a traditional Chinese ink wash painting style. "
            "Use varied brush stroke widths, ink splatter effects, and leave generous "
            "white space. Grayscale only, mimicking rice-paper texture."
        ),
    },
]


def _encode_image_base64(img_path: str) -> str:
    """读取图片文件并转为 base64 编码字符串。"""
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


class AIGenerator:
    """
    AI 线稿生成器 — 支持 OpenAI / Stable Diffusion / 自定义接口。

    api_provider: "openai" | "sd" | "custom"
    api_url:  接口地址
    api_key:  API 密钥
    prompt:   生成提示词
    """

    def __init__(
        self,
        api_provider: str = "openai",
        api_url: str = "",
        api_key: str = "",
        prompt: str = "",
        timeout: int = 120,
    ):
        self.api_provider = api_provider
        self.api_url = api_url
        self.api_key = api_key
        self.prompt = prompt or PRESET_PROMPTS[0]["prompt"]
        self.timeout = timeout

    # ──────────── public ────────────

    def generate(self, img_path: str) -> str:
        """
        对输入图片调用 AI API，返回生成线稿的本地保存路径。
        """
        provider = (self.api_provider or "").lower()

        if provider == "openai":
            result_bytes = self._call_openai(img_path)
        elif provider == "sd":
            result_bytes = self._call_sd(img_path)
        else:
            result_bytes = self._call_custom(img_path)

        # 保存结果
        out_dir = os.path.join(os.path.dirname(img_path), "out_sketch")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "ai_sketch.png")

        # 解码并存为灰度线稿
        img = decode_image_bytes(result_bytes, grayscale=True)
        if img is None:
            raise RuntimeError("AI 返回的图片无法解码，请检查接口配置。")

        bw = threshold_binary(img, 127, invert=False)
        imwrite_unicode(out_path, bw)
        return out_path

    # ──────────── OpenAI ────────────

    def _call_openai(self, img_path: str) -> bytes:
        url = self.api_url or "https://api.openai.com/v1/images/generations"
        if not self.api_key:
            raise RuntimeError("请在设置中填写 OpenAI API Key。")

        payload = json.dumps({
            "model": "dall-e-3",
            "prompt": self.prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "b64_json",
        }).encode("utf-8")

        req = urllib_request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        return self._fetch(req, provider="openai")

    # ──────────── Stable Diffusion ────────────

    def _call_sd(self, img_path: str) -> bytes:
        url = self.api_url or "http://127.0.0.1:7860/sdapi/v1/img2img"
        img_b64 = _encode_image_base64(img_path)

        payload = json.dumps({
            "init_images": [img_b64],
            "prompt": self.prompt,
            "negative_prompt": "color, shading, gradient, photo, realistic",
            "steps": 30,
            "cfg_scale": 7.5,
            "denoising_strength": 0.75,
            "width": 512,
            "height": 512,
        }).encode("utf-8")

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = urllib_request.Request(url, data=payload, headers=headers, method="POST")
        return self._fetch(req, provider="sd")

    # ──────────── 自定义接口 ────────────

    def _call_custom(self, img_path: str) -> bytes:
        if not self.api_url:
            raise RuntimeError("请在设置中填写自定义 API 地址。")

        img_b64 = _encode_image_base64(img_path)
        payload = json.dumps({
            "image": img_b64,
            "prompt": self.prompt,
        }).encode("utf-8")

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = urllib_request.Request(self.api_url, data=payload, headers=headers, method="POST")
        return self._fetch(req)

    # ──────────── 通用请求 ────────────

    def _fetch(self, req: urllib_request.Request, provider: str = "") -> bytes:
        try:
            with urllib_request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read()
        except HTTPError as e:
            raise RuntimeError(f"AI API 返回错误 {e.code}: {e.read().decode(errors='replace')[:500]}")
        except URLError as e:
            raise RuntimeError(f"无法连接 AI API: {e.reason}")

        # 解析响应
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            # 直接返回原始字节（可能是纯图片响应）
            return body

        if provider == "sd":
            images = data.get("images", [])
            if images:
                return base64.b64decode(images[0])

        # OpenAI images API
        if provider == "openai":
            result_data = data.get("data", [])
            if result_data:
                b64 = result_data[0].get("b64_json", "")
                if b64:
                    return base64.b64decode(b64)
                img_url = result_data[0].get("url", "")
                if img_url:
                    with urllib_request.urlopen(img_url, timeout=self.timeout) as r:
                        return r.read()

        # Generic / custom response formats
        result_data = data.get("data", [])
        if result_data:
            b64 = result_data[0].get("b64_json", "")
            if b64:
                return base64.b64decode(b64)
            img_url = result_data[0].get("url", "")
            if img_url:
                with urllib_request.urlopen(img_url, timeout=self.timeout) as r:
                    return r.read()

        # 如果 json 里有 image 字段
        if "image" in data:
            return base64.b64decode(data["image"])

        raise RuntimeError("AI API 返回了无法识别的格式。")
