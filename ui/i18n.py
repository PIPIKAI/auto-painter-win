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
            "<h3>AutoPainter v{}</h3>"
            "<p>线稿生成与自动绘画工具</p>"
            "<p>支持多种线稿风格生成，并可自动控制鼠标进行绘画。</p>"
            "<p>开源地址: <a href='https://github.com/PIPIKAI/auto-painter-win'>GitHub</a></p>"
        ),

        # 欢迎/免责声明
        "welcome_title": "使用须知",
        "welcome_message": (
            "<h3>AutoPainter 完全免费、开源</h3>"
            "<p>本软件无广告、无付费功能。按「原样」提供，不保证适用于所有场景，使用风险由您自行承担，请勿用于非法用途。</p>"
            "<p><b>快速开始：</b></p>"
            "<ul>"
            "<li>可在“设置”中修改绘图快捷键、AI 接口等偏好。</li>"
            "<li>基本流程：选择图片 → 生成线稿 → 记录画布左上/右下角 → 开始绘画。</li>"
            "<li>绘制过程中可随时按停止/中断键终止。</li>"
            "</ul>"
        ),
        "welcome_hint": "点击下方“我已知晓”后方可继续使用。",
        "welcome_confirm": "我已知晓",
        # “{}” 是格式化占位符，会被剩余秒数替换
        "welcome_confirm_countdown": "我已知晓 ({})",

        # 状态栏
        "status_ready": "就绪 - 请选择一张图片开始",
        "status_image_loaded": "已加载图片: {}",
        "status_generating": "正在生成线稿...",
        "status_generate_done": "线稿生成完成！",
        "status_generate_fail": "生成失败: {}",
        "status_saved": "线稿已保存: {}",
        "status_painting_countdown": "将在 {} 秒后开始绘画，请切换到目标窗口...",
        "status_painting_prepare": "开始绘画后，请按热键依次记录画布左上角和右下角",
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
        "lbl_paint_mode": "绘画模式:",
        "radio_draw_sketch": "画线稿",
        "radio_write_text": "写字",
        "lbl_speed": "绘画速度:",
        "lbl_draw_button": "画笔按键:",
        "draw_button_left": "左键",
        "draw_button_right": "右键",
        "group_hotkeys": "⌨️ 热键设置",
        "lbl_start_hotkey": "开始绘画:",
        "lbl_calib_start": "记录左上角:",
        "lbl_calib_end": "记录右下角:",
        "lbl_abort_hotkey": "停止/中断:",
        "btn_start_paint": "▶ 开始绘画",
        "btn_stop_paint": "⏹ 停止",

        # 写字模式
        "group_text": "✍️ 写字设置",
        "lbl_text_input": "输入文字:",
        "placeholder_text": "在此输入要写的文字...",
        "lbl_font": "字体:",
        "lbl_font_size": "字号:",
        "btn_preview_text": "预览文字",
        "status_text_rendered": "文字渲染完成，可以开始绘画",
        "status_text_empty": "请先输入要写的文字",

        # 历史记录
        "group_history": "📋 历史记录",
        "history_empty": "暂无历史记录",
        "history_menu_load": "加载此线稿",
        "history_menu_paint": "直接绘画",
        "history_menu_export": "导出图片",
        "history_menu_delete": "删除",
        "history_menu_clear": "清空所有历史",
        "history_loaded": "已加载历史线稿",
        "history_deleted": "已删除历史记录",
        "history_cleared": "已清空所有历史记录",
        "history_exported": "已导出: {}",
        "history_skipped_duplicate": "与已有记录相同，已跳过",
        
        "font_simsun": "宋体 (SimSun)",
        "font_simhei": "黑体 (SimHei)",
        "font_msyh": "微软雅黑 (Microsoft YaHei)",
        "font_kaiti": "楷体 (KaiTi)",
        "font_fangsong": "仿宋 (FangSong)",
        "font_arial": "Arial",
        "font_times": "Times New Roman",
        "font_comic": "Comic Sans MS",
        "font_courier": "Courier New",

        # 预览面板
        "tab_compare": "🔀 对比视图",
        "tab_original": "📷 原始图片",
        "tab_sketch": "✏️ 线稿",
        "lbl_original_title": "📷 原始图片",
        "lbl_sketch_title": "✏️ 线稿预览",
        "placeholder_select": "请从左侧选择一张图片",
        "placeholder_sketch": "生成线稿后在此预览",

        # 设置对话框
        "menu_settings": "设置(&S)",
        "btn_settings_open": "设置",
        "settings_title": "⚙️ 设置",
        "settings_tab_hotkeys": "⌨️ 快捷键",
        "settings_tab_ai": "🤖 AI 画图",
        "settings_save": "保存",
        "settings_cancel": "取消",
        "settings_saved": "设置已保存",

        # AI 设置
        "ai_provider": "AI 接口:",
        "ai_api_url": "API 地址:",
        "ai_api_key": "API 密钥:",
        "ai_prompt": "生成提示词:",
        "ai_preset_prompts": "预设提示词:",
        "ai_select_preset": "-- 选择预设 --",
        "ai_api_url_hint_openai": "默认: https://api.openai.com/v1/images/generations",
        "ai_api_url_hint_sd": "默认: http://127.0.0.1:7860/sdapi/v1/img2img",
        "ai_api_url_hint_custom": "请输入自定义接口地址",
        "ai_prompt_placeholder": "在此输入生成提示词...",

        # 历史还原
        "history_restored": "已还原历史记录的设置和图片",

        # 更新检查
        "update_title": "发现新版本",
        "update_message": "发现新版本 <b>{}</b>（当前版本: {}）<br><br>是否前往下载页面？",
        "update_download": "前往下载",
        "update_skip": "暂不更新",
        "update_checking": "正在检查更新...",
        "update_latest": "当前已是最新版本",
        "update_error": "检查更新失败: {}",

        # 通知设置
        "settings_tab_general": "🔔 通用",
        "group_notifications": "🔔 通知设置",
        "notify_paint_progress": "绘画进度通知",
        "notify_paint_progress_hint": "在绘画进度达到 25%、50%、75% 时在系统托盘显示通知",
        "notify_operation_tips": "操作提示通知",
        "notify_operation_tips_hint": "在绘画开始/完成等操作时在系统托盘显示通知",
        "group_about": "ℹ️ 关于",
        "about_version_label": "版本: {}",
        "about_homepage": "项目主页",
        "about_check_update": "检查更新",
        "about_description": "AutoPainter 是一款免费开源的线稿生成与自动绘画工具。",
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
            "<h3>AutoPainter v{}</h3>"
            "<p>Sketch generation and auto-drawing tool.</p>"
            "<p>Supports multiple sketch styles and automated mouse-controlled painting.</p>"
            "<p>Source: <a href='https://github.com/PIPIKAI/auto-painter-win'>GitHub</a></p>"
        ),

        # Welcome / disclaimer
        "welcome_title": "Welcome & Disclaimer",
        "welcome_message": (
            "<h3>AutoPainter is free & open source</h3>"
            "<p>No ads, no paid features. Provided as-is without warranties; use at your own risk and avoid illegal use.</p>"
            "<p><b>Quick tips:</b></p>"
            "<ul>"
            "<li>Adjust drawing hotkeys and AI preferences in Settings.</li>"
            "<li>Basic flow: choose an image → generate sketch → record canvas top-left/bottom-right → start painting.</li>"
            "<li>You can press Stop/Abort at any time to cancel painting.</li>"
            "</ul>"
        ),
        "welcome_hint": "Please confirm below to continue using the app.",
        "welcome_confirm": "Got it",
        # "{}" is a format placeholder that will be replaced with remaining seconds
        "welcome_confirm_countdown": "Got it ({})",

        # Status bar
        "status_ready": "Ready - Please select an image to start",
        "status_image_loaded": "Image loaded: {}",
        "status_generating": "Generating sketch...",
        "status_generate_done": "Sketch generated successfully!",
        "status_generate_fail": "Generation failed: {}",
        "status_saved": "Sketch saved: {}",
        "status_painting_countdown": "Painting starts in {} seconds, switch to target window...",
        "status_painting_prepare": "After starting, use the hotkeys to record the top-left and bottom-right corners",
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
        "lbl_paint_mode": "Paint Mode:",
        "radio_draw_sketch": "Draw Sketch",
        "radio_write_text": "Write Text",
        "lbl_speed": "Paint Speed:",
        "lbl_draw_button": "Draw Button:",
        "draw_button_left": "Left Button",
        "draw_button_right": "Right Button",
        "group_hotkeys": "⌨️ Hotkeys",
        "lbl_start_hotkey": "Start painting:",
        "lbl_calib_start": "Mark top-left:",
        "lbl_calib_end": "Mark bottom-right:",
        "lbl_abort_hotkey": "Abort/stop:",
        "btn_start_paint": "▶ Start Painting",
        "btn_stop_paint": "⏹ Stop",

        # Text mode
        "group_text": "✍️ Text Settings",
        "lbl_text_input": "Input Text:",
        "placeholder_text": "Type text to write here...",
        "lbl_font": "Font:",
        "lbl_font_size": "Font Size:",
        "btn_preview_text": "Preview Text",
        "status_text_rendered": "Text rendered, ready to paint",
        "status_text_empty": "Please enter text first",

        "font_simsun": "SimSun",
        "font_simhei": "SimHei",
        "font_msyh": "Microsoft YaHei",
        "font_kaiti": "KaiTi",
        "font_fangsong": "FangSong",
        "font_arial": "Arial",
        "font_times": "Times New Roman",
        "font_comic": "Comic Sans MS",
        "font_courier": "Courier New",
        
        # History
        "group_history": "📋 History",
        "history_empty": "No history yet",
        "history_menu_load": "Load Sketch",
        "history_menu_paint": "Paint Directly",
        "history_menu_export": "Export Image",
        "history_menu_delete": "Delete",
        "history_menu_clear": "Clear All History",
        "history_loaded": "History sketch loaded",
        "history_deleted": "History entry deleted",
        "history_cleared": "All history cleared",
        "history_exported": "Exported: {}",
        "history_skipped_duplicate": "Skipped duplicate entry",

        # Preview panel
        "tab_compare": "🔀 Compare View",
        "tab_original": "📷 Original Image",
        "tab_sketch": "✏️ Sketch",
        "lbl_original_title": "📷 Original Image",
        "lbl_sketch_title": "✏️ Sketch Preview",
        "placeholder_select": "Select an image from the left panel",
        "placeholder_sketch": "Sketch preview will appear here",

        # Settings dialog
        "menu_settings": "&Settings",
        "btn_settings_open": "Settings",
        "settings_title": "⚙️ Settings",
        "settings_tab_hotkeys": "⌨️ Hotkeys",
        "settings_tab_ai": "🤖 AI Drawing",
        "settings_save": "Save",
        "settings_cancel": "Cancel",
        "settings_saved": "Settings saved",

        # AI settings
        "ai_provider": "AI Provider:",
        "ai_api_url": "API URL:",
        "ai_api_key": "API Key:",
        "ai_prompt": "Generation Prompt:",
        "ai_preset_prompts": "Preset Prompts:",
        "ai_select_preset": "-- Select Preset --",
        "ai_api_url_hint_openai": "Default: https://api.openai.com/v1/images/generations",
        "ai_api_url_hint_sd": "Default: http://127.0.0.1:7860/sdapi/v1/img2img",
        "ai_api_url_hint_custom": "Enter custom API URL",
        "ai_prompt_placeholder": "Enter your prompt here...",

        # History restore
        "history_restored": "Restored settings and images from history",

        # Update check
        "update_title": "New Version Available",
        "update_message": "New version <b>{}</b> available (current: {})<br><br>Would you like to go to the download page?",
        "update_download": "Go to Download",
        "update_skip": "Skip",
        "update_checking": "Checking for updates...",
        "update_latest": "You are using the latest version",
        "update_error": "Failed to check for updates: {}",

        # Notification settings
        "settings_tab_general": "🔔 General",
        "group_notifications": "🔔 Notifications",
        "notify_paint_progress": "Paint progress notifications",
        "notify_paint_progress_hint": "Show tray notifications at 25%, 50%, 75% painting progress",
        "notify_operation_tips": "Operation tips notifications",
        "notify_operation_tips_hint": "Show tray notifications for painting start/complete events",
        "group_about": "ℹ️ About",
        "about_version_label": "Version: {}",
        "about_homepage": "Homepage",
        "about_check_update": "Check for Updates",
        "about_description": "AutoPainter is a free, open-source sketch generation and auto-drawing tool.",
    },
}


class I18n(QObject):
    """全局单例翻译管理器。"""

    language_changed = pyqtSignal(str)

    _instance = None
    _qt_initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
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
