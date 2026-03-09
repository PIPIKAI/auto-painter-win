"""
多语言翻译管理器
支持中文 (zh_CN) 和英文 (en_US)
"""
from PyQt5.QtCore import QObject, pyqtSignal


# ──────────────── 语言包 ────────────────

TRANSLATIONS = {
    "zh_CN": {
        # 窗口
        "app_title": "🎨 AutoPainter - 线稿生成与自动绘画",

        # 菜单栏
        "menu_file": "文件(&F)",
        "menu_open": "打开图片(&O)",
        "menu_save": "保存线稿(&S)",
        "menu_exit": "退出(&Q)",
        "menu_help": "帮助(&H)",
        "menu_about": "关于(&A)",
        "menu_language": "语言(&L)",
        "lang_zh": "中文",
        "lang_en": "English",

        # 关于对话框
        "about_title": "关于 AutoPainter",
        "about_content": (
            "<h3>AutoPainter v1.0</h3>"
            "<p>线稿生成与自动绘画工具</p>"
            "<p>支持多种线稿风格生成，并可自动控制鼠标进行绘画。</p>"
        ),

        # 状态栏
        "status_ready": "就绪 - 请选择一张图片开始",
        "status_image_loaded": "已加载图片: {}",
        "status_generating": "正在生成线稿...",
        "status_generate_done": "线稿生成完成！",
        "status_generate_fail": "生成失败: {}",
        "status_saved": "线稿已保存: {}",
        "status_painting_countdown": "将在 {} 秒后开始绘画，请切换到目标窗口...",
        "status_painting_progress": "绘画进度: {}%",
        "status_painting_done": "绘画完成！",
        "status_painting_error": "绘画出错: {}",
        "status_painting_stopped": "绘画已停止",

        # 控制面板 - 图片选择
        "group_image": "📁 图片选择",
        "btn_select_image": "选择图片",
        "lbl_no_file": "未选择文件",
        "lbl_drop_hint": "拖拽或点击选择图片",
        "dialog_open_title": "选择图片",
        "dialog_open_filter": "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*)",

        # 控制面板 - 线稿风格
        "group_style": "🎨 线稿风格",
        "style_pencil": "✏️ 铅笔素描",
        "style_pen": "🖊️ 钢笔线稿",
        "style_ink": "🖌️ 水墨风格",
        "style_comic": "💥 漫画风格",
        "style_contour": "〰️ 轮廓提取",
        "style_ai": "🤖 AI 生成",
        "lbl_api": "API 接口:",
        "api_dalle": "OpenAI DALL-E",
        "api_sd": "Stable Diffusion",
        "api_custom": "自定义接口",

        # 控制面板 - 参数调整
        "group_params": "⚙️ 参数调整",
        "lbl_thickness": "线条粗细:",
        "lbl_contrast": "对比度:",
        "lbl_threshold": "阈值:",
        "chk_invert": "反色输出",

        # 控制面板 - 生成
        "group_generate": "🖼️ 生成",
        "btn_generate": "生成线稿",
        "btn_generating": "生成中...",
        "btn_save": "保存线稿",
        "dialog_save_title": "保存线稿",
        "dialog_save_filter": "PNG 图片 (*.png);;JPEG 图片 (*.jpg);;所有文件 (*)",

        # 控制面板 - 绘画控制
        "group_paint": "🖱️ 自动绘画控制",
        "lbl_speed": "绘画速度:",
        "lbl_delay": "起笔延迟 (秒):",
        "suffix_seconds": " 秒",
        "lbl_scale": "画布缩放:",
        "btn_start_paint": "▶ 开始绘画",
        "btn_stop_paint": "⏹ 停止",

        # 预览面板
        "tab_compare": "🔀 对比视图",
        "tab_original": "📷 原始图片",
        "tab_sketch": "✏️ 线稿",
        "lbl_original_title": "📷 原始图片",
        "lbl_sketch_title": "✏️ 线稿预览",
        "placeholder_select": "请从左侧选择一张图片",
        "placeholder_sketch": "生成线稿后在此预览",
    },

    "en_US": {
        # Window
        "app_title": "🎨 AutoPainter - Sketch Generator & Auto Drawing",

        # Menu bar
        "menu_file": "&File",
        "menu_open": "&Open Image",
        "menu_save": "&Save Sketch",
        "menu_exit": "&Quit",
        "menu_help": "&Help",
        "menu_about": "&About",
        "menu_language": "&Language",
        "lang_zh": "中文",
        "lang_en": "English",

        # About dialog
        "about_title": "About AutoPainter",
        "about_content": (
            "<h3>AutoPainter v1.0</h3>"
            "<p>Sketch generation and auto-drawing tool.</p>"
            "<p>Supports multiple sketch styles and automated mouse-controlled painting.</p>"
        ),

        # Status bar
        "status_ready": "Ready - Please select an image to start",
        "status_image_loaded": "Image loaded: {}",
        "status_generating": "Generating sketch...",
        "status_generate_done": "Sketch generated successfully!",
        "status_generate_fail": "Generation failed: {}",
        "status_saved": "Sketch saved: {}",
        "status_painting_countdown": "Painting starts in {} seconds, switch to target window...",
        "status_painting_progress": "Painting progress: {}%",
        "status_painting_done": "Painting complete!",
        "status_painting_error": "Painting error: {}",
        "status_painting_stopped": "Painting stopped",

        # Control panel - Image selection
        "group_image": "📁 Image Selection",
        "btn_select_image": "Select Image",
        "lbl_no_file": "No file selected",
        "lbl_drop_hint": "Drag & drop or click to select",
        "dialog_open_title": "Select Image",
        "dialog_open_filter": "Image Files (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*)",

        # Control panel - Sketch style
        "group_style": "🎨 Sketch Style",
        "style_pencil": "✏️ Pencil Sketch",
        "style_pen": "🖊️ Pen Drawing",
        "style_ink": "🖌️ Ink Wash",
        "style_comic": "💥 Comic Style",
        "style_contour": "〰️ Contour Extraction",
        "style_ai": "🤖 AI Generated",
        "lbl_api": "API Provider:",
        "api_dalle": "OpenAI DALL-E",
        "api_sd": "Stable Diffusion",
        "api_custom": "Custom API",

        # Control panel - Parameters
        "group_params": "⚙️ Parameters",
        "lbl_thickness": "Line Thickness:",
        "lbl_contrast": "Contrast:",
        "lbl_threshold": "Threshold:",
        "chk_invert": "Invert Output",

        # Control panel - Generate
        "group_generate": "🖼️ Generate",
        "btn_generate": "Generate Sketch",
        "btn_generating": "Generating...",
        "btn_save": "Save Sketch",
        "dialog_save_title": "Save Sketch",
        "dialog_save_filter": "PNG Image (*.png);;JPEG Image (*.jpg);;All Files (*)",

        # Control panel - Paint control
        "group_paint": "🖱️ Auto Paint Control",
        "lbl_speed": "Paint Speed:",
        "lbl_delay": "Start Delay (sec):",
        "suffix_seconds": " sec",
        "lbl_scale": "Canvas Scale:",
        "btn_start_paint": "▶ Start Painting",
        "btn_stop_paint": "⏹ Stop",

        # Preview panel
        "tab_compare": "🔀 Compare View",
        "tab_original": "📷 Original Image",
        "tab_sketch": "✏️ Sketch",
        "lbl_original_title": "📷 Original Image",
        "lbl_sketch_title": "✏️ Sketch Preview",
        "placeholder_select": "Select an image from the left panel",
        "placeholder_sketch": "Sketch preview will appear here",
    },
}


class I18n(QObject):
    """
    全局单例翻译管理器。
    """

    language_changed = pyqtSignal(str)

    _instance = None
    _qt_initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 必须每次都调用 super().__init__()，QObject 需要它
        # 但用 _qt_initialized 防止重复设置属性
        if not I18n._qt_initialized:
            super().__init__()
            I18n._qt_initialized = True
            self._language = "zh_CN"

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, lang_code: str):
        if lang_code not in TRANSLATIONS:
            raise ValueError(f"Unsupported language: {lang_code}")
        if lang_code != self._language:
            self._language = lang_code
            self.language_changed.emit(lang_code)

    def t(self, key: str, *args) -> str:
        """
        获取翻译文本。
        支持带占位符:  i18n.t("status_image_loaded", filename)
        """
        text = TRANSLATIONS.get(self._language, {}).get(key)
        if text is None:
            text = TRANSLATIONS.get("zh_CN", {}).get(key, key)
        if args:
            try:
                text = text.format(*args)
            except (IndexError, KeyError):
                pass
        return text

    def available_languages(self) -> list:
        return list(TRANSLATIONS.keys())


# 全局单例
i18n = I18n()