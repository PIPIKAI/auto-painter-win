"""
左侧控制面板 - 包含所有操作按钮和参数调整
"""
import os
import json

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QSlider, QComboBox,
    QFileDialog, QSpinBox, QCheckBox, QProgressBar,
    QScrollArea, QFrame, QRadioButton, QButtonGroup,
    QShortcut
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QPixmap, QKeySequence

from ui.i18n import i18n
from ui.app_paths import SETTINGS_PATH
from ui.settings_dialog import load_settings, save_settings
from core.sketch_generator import SketchGenerator
from core.auto_painter import AutoPainter, PainterConfig, PaintCancelled
from ui.text_panel import TextPanel


CANCELLED_SENTINEL = "__cancelled__"
DEFAULT_DRAW_BUTTON_SIDE = "right"


class SketchWorker(QThread):
    """线稿生成工作线程"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, image_path, style, params):
        super().__init__()
        self.image_path = image_path
        self.style = style
        self.params = params
        self.generator = SketchGenerator()

    def run(self):
        try:
            result = self.generator.generate(self.image_path, self.style, self.params)
            self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))


class AISketchWorker(QThread):
    """AI 线稿生成工作线程"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, image_path, ai_settings):
        super().__init__()
        self.image_path = image_path
        self.ai_settings = ai_settings

    def run(self):
        try:
            from core.ai_generator import AIGenerator
            gen = AIGenerator(
                api_provider=self.ai_settings.get("provider", "openai"),
                api_url=self.ai_settings.get("api_url", ""),
                api_key=self.ai_settings.get("api_key", ""),
                prompt=self.ai_settings.get("prompt", ""),
            )
            result = gen.generate(self.image_path)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class PaintWorker(QThread):
    """自动绘画工作线程"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, sketch_data, params):
        super().__init__()
        self.sketch_data = sketch_data
        self.params = params
        self._is_running = True
        self._painter = None

    def run(self):
        try:
            config = PainterConfig.from_params(self.params)
            self._painter = AutoPainter(
                self.sketch_data,
                config,
                stop_checker=lambda: not self._is_running,
            )
            self._painter.start(
                progress_callback=self.progress.emit,
                status_callback=self.status.emit,
            )
            self.finished.emit()
        except PaintCancelled:
            self.error.emit(CANCELLED_SENTINEL)
        except Exception as e:
            print(str(e))
            self.error.emit(str(e))

    def stop(self):
        self._is_running = False
        if self._painter:
            self._painter.request_stop()


class ControlPanel(QWidget):
    """控制面板"""
    image_selected = pyqtSignal(str)
    sketch_generated = pyqtSignal(object)
    painting_progress = pyqtSignal(int)
    status_message = pyqtSignal(str)
    notification_message = pyqtSignal(str)

    # 新增：通知主窗口保存历史
    history_entry = pyqtSignal(str, str, str, dict)  # sketch_path, source_path, style, params
    settings_requested = pyqtSignal()

    STYLE_KEYS = [
        ("pencil",  "style_pencil"),
        ("pen",     "style_pen"),
        ("ink",     "style_ink"),
        ("comic",   "style_comic"),
        ("contour", "style_contour"),
        ("ai",      "style_ai"),
    ]

    def __init__(self):
        super().__init__()
        self._image_path = None
        self._sketch_data = None
        self._sketch_worker = None
        self._paint_worker = None
        self._paint_mode = "sketch"  # "sketch" 或 "text"
        self._start_shortcut = None
        self._pending_history_entry = None  # (sketch_path, source_path, style, params)

        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._on_generate)

        self._init_ui()
        self._load_hotkey_settings()
        i18n.language_changed.connect(self._retranslate)

    def _init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # ═══ 顶部操作 ═══
        top_row = QHBoxLayout()
        top_row.addStretch()
        self.btn_settings = QPushButton(i18n.t("btn_settings_open"))
        self.btn_settings.setObjectName("primaryButton")
        self.btn_settings.setFixedHeight(34)
        self.btn_settings.clicked.connect(self.settings_requested.emit)
        top_row.addWidget(self.btn_settings)
        layout.addLayout(top_row)

        # ═══ 图片选择 ═══
        self.grp_image = QGroupBox()
        img_layout = QVBoxLayout()

        self.btn_select = QPushButton()
        self.btn_select.setObjectName("primaryButton")
        self.btn_select.clicked.connect(self._on_select_image)
        img_layout.addWidget(self.btn_select)

        self.lbl_filename = QLabel()
        self.lbl_filename.setWordWrap(True)
        self.lbl_filename.setStyleSheet("color: #888; font-size: 12px;")
        img_layout.addWidget(self.lbl_filename)

        self.lbl_thumbnail = QLabel()
        self.lbl_thumbnail.setFixedHeight(150)
        self.lbl_thumbnail.setAlignment(Qt.AlignCenter)
        self.lbl_thumbnail.setStyleSheet(
            "border: 1px dashed #ccc; border-radius: 4px; background: #fafafa;"
        )
        img_layout.addWidget(self.lbl_thumbnail)

        self.grp_image.setLayout(img_layout)
        layout.addWidget(self.grp_image)

        # ═══ 线稿风格 ═══
        self.grp_style = QGroupBox()
        style_layout = QVBoxLayout()

        self.combo_style = QComboBox()
        style_layout.addWidget(self.combo_style)

        self.combo_style.currentIndexChanged.connect(self._on_style_changed)

        self.grp_style.setLayout(style_layout)
        layout.addWidget(self.grp_style)

        # ═══ 参数调整 ═══
        self.grp_params = QGroupBox()
        param_layout = QVBoxLayout()

        self.lbl_thickness = QLabel()
        param_layout.addWidget(self.lbl_thickness)
        self.slider_thickness = QSlider(Qt.Horizontal)
        self.slider_thickness.setRange(1, 10)
        self.slider_thickness.setValue(3)
        self.slider_thickness.setSingleStep(1)
        self.slider_thickness.setPageStep(1)
        self.spin_thickness = QSpinBox()
        self.spin_thickness.setRange(1, 10)
        self.spin_thickness.setValue(3)
        self.spin_thickness.setFixedWidth(55)
        h1 = QHBoxLayout()
        h1.addWidget(self.slider_thickness)
        h1.addWidget(self.spin_thickness)
        param_layout.addLayout(h1)
        self.slider_thickness.valueChanged.connect(self.spin_thickness.setValue)
        self.spin_thickness.valueChanged.connect(self.slider_thickness.setValue)
        self.slider_thickness.valueChanged.connect(self._on_param_changed)

        self.lbl_contrast = QLabel()
        param_layout.addWidget(self.lbl_contrast)
        self.slider_contrast = QSlider(Qt.Horizontal)
        self.slider_contrast.setRange(0, 100)
        self.slider_contrast.setValue(50)
        self.slider_contrast.setSingleStep(1)
        self.slider_contrast.setPageStep(1)
        self.spin_contrast = QSpinBox()
        self.spin_contrast.setRange(0, 100)
        self.spin_contrast.setValue(50)
        self.spin_contrast.setFixedWidth(55)
        h2 = QHBoxLayout()
        h2.addWidget(self.slider_contrast)
        h2.addWidget(self.spin_contrast)
        param_layout.addLayout(h2)
        self.slider_contrast.valueChanged.connect(self.spin_contrast.setValue)
        self.spin_contrast.valueChanged.connect(self.slider_contrast.setValue)
        self.slider_contrast.valueChanged.connect(self._on_param_changed)

        self.lbl_threshold = QLabel()
        param_layout.addWidget(self.lbl_threshold)
        self.slider_threshold = QSlider(Qt.Horizontal)
        self.slider_threshold.setRange(0, 255)
        self.slider_threshold.setValue(127)
        self.slider_threshold.setSingleStep(1)
        self.slider_threshold.setPageStep(1)
        self.spin_threshold = QSpinBox()
        self.spin_threshold.setRange(0, 255)
        self.spin_threshold.setValue(127)
        self.spin_threshold.setFixedWidth(55)
        h3 = QHBoxLayout()
        h3.addWidget(self.slider_threshold)
        h3.addWidget(self.spin_threshold)
        param_layout.addLayout(h3)
        self.slider_threshold.valueChanged.connect(self.spin_threshold.setValue)
        self.spin_threshold.valueChanged.connect(self.slider_threshold.setValue)
        self.slider_threshold.valueChanged.connect(self._on_param_changed)

        self.chk_invert = QCheckBox()
        param_layout.addWidget(self.chk_invert)
        self.chk_invert.stateChanged.connect(self._on_param_changed)

        self.grp_params.setLayout(param_layout)
        layout.addWidget(self.grp_params)

        # ═══ 生成 ═══
        self.grp_generate = QGroupBox()
        gen_layout = QVBoxLayout()

        self.btn_generate = QPushButton()
        self.btn_generate.setObjectName("primaryButton")
        self.btn_generate.setEnabled(False)
        self.btn_generate.clicked.connect(self._on_generate)
        gen_layout.addWidget(self.btn_generate)

        self.btn_save = QPushButton()
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._on_save_sketch)
        gen_layout.addWidget(self.btn_save)

        self.grp_generate.setLayout(gen_layout)
        layout.addWidget(self.grp_generate)

        # ═══ 绘画控制 ═══
        self.grp_paint = QGroupBox()
        paint_layout = QVBoxLayout()

        # 模式切换：画线稿 / 写字
        self.lbl_paint_mode = QLabel()
        paint_layout.addWidget(self.lbl_paint_mode)

        mode_row = QHBoxLayout()
        self.radio_sketch = QRadioButton()
        self.radio_sketch.setChecked(True)
        self.radio_text = QRadioButton()

        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.radio_sketch, 0)
        self.mode_group.addButton(self.radio_text, 1)
        self.mode_group.buttonClicked.connect(self._on_mode_changed)

        mode_row.addWidget(self.radio_sketch)
        mode_row.addWidget(self.radio_text)
        mode_row.addStretch()
        paint_layout.addLayout(mode_row)

        # 写字面板（默认隐藏）
        self.text_panel = TextPanel()
        self.text_panel.setVisible(False)
        self.text_panel.text_rendered.connect(self._on_text_rendered)
        self.text_panel.status_message.connect(lambda msg: self.status_message.emit(msg))
        paint_layout.addWidget(self.text_panel)

        # 绘画速度
        self.lbl_speed = QLabel()
        paint_layout.addWidget(self.lbl_speed)
        self.slider_speed = QSlider(Qt.Horizontal)
        self.slider_speed.setRange(1, 100)
        self.slider_speed.setValue(50)
        self.lbl_speed_val = QLabel("50")
        h4 = QHBoxLayout()
        h4.addWidget(self.slider_speed)
        h4.addWidget(self.lbl_speed_val)
        paint_layout.addLayout(h4)
        self.slider_speed.valueChanged.connect(
            lambda v: self.lbl_speed_val.setText(str(v))
        )

        self.lbl_draw_button = QLabel()
        paint_layout.addWidget(self.lbl_draw_button)
        draw_row = QHBoxLayout()
        self.btn_draw_left = QPushButton()
        self.btn_draw_left.setObjectName("segButton")
        self.btn_draw_left.setCheckable(True)
        self.btn_draw_right = QPushButton()
        self.btn_draw_right.setObjectName("segButton")
        self.btn_draw_right.setCheckable(True)
        self.draw_button_group = QButtonGroup(self)
        self.draw_button_group.setExclusive(True)
        self.draw_button_group.addButton(self.btn_draw_left, 0)
        self.draw_button_group.addButton(self.btn_draw_right, 1)
        self.btn_draw_left.clicked.connect(lambda: self._on_draw_button_changed("left"))
        self.btn_draw_right.clicked.connect(lambda: self._on_draw_button_changed("right"))
        draw_row.addWidget(self.btn_draw_left)
        draw_row.addWidget(self.btn_draw_right)
        draw_row.addStretch()
        paint_layout.addLayout(draw_row)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        paint_layout.addWidget(self.progress_bar)

        # 按钮
        btn_row = QHBoxLayout()
        self.btn_start_paint = QPushButton()
        self.btn_start_paint.setObjectName("successButton")
        self.btn_start_paint.setEnabled(False)
        self.btn_start_paint.clicked.connect(self._on_start_painting)
        btn_row.addWidget(self.btn_start_paint)

        self.btn_stop_paint = QPushButton()
        self.btn_stop_paint.setObjectName("dangerButton")
        self.btn_stop_paint.setEnabled(False)
        self.btn_stop_paint.clicked.connect(self._on_stop_painting)
        btn_row.addWidget(self.btn_stop_paint)

        paint_layout.addLayout(btn_row)

        self.grp_paint.setLayout(paint_layout)
        layout.addWidget(self.grp_paint)

        # 初始化热键快捷方式
        self._refresh_hotkeys()

        layout.addStretch()
        scroll.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 初始翻译
        self._retranslate()

    # ──────────── 翻译刷新 ────────────

    def _retranslate(self, _lang=None):
        self.grp_image.setTitle(i18n.t("group_image"))
        self.btn_select.setText(i18n.t("btn_select_image"))
        if not self._image_path:
            self.lbl_filename.setText(i18n.t("lbl_no_file"))
            self.lbl_thumbnail.setText(i18n.t("lbl_drop_hint"))

        self.grp_style.setTitle(i18n.t("group_style"))
        current_idx = self.combo_style.currentIndex()
        self.combo_style.blockSignals(True)
        self.combo_style.clear()
        for key, i18n_key in self.STYLE_KEYS:
            self.combo_style.addItem(i18n.t(i18n_key), key)
        self.combo_style.setCurrentIndex(max(0, current_idx))
        self.combo_style.blockSignals(False)

        self.grp_params.setTitle(i18n.t("group_params"))
        self.lbl_thickness.setText(i18n.t("lbl_thickness"))
        self.lbl_contrast.setText(i18n.t("lbl_contrast"))
        self.lbl_threshold.setText(i18n.t("lbl_threshold"))
        self.chk_invert.setText(i18n.t("chk_invert"))

        self.grp_generate.setTitle(i18n.t("group_generate"))
        self.btn_generate.setText(i18n.t("btn_generate"))
        self.btn_save.setText(i18n.t("btn_save"))

        self.grp_paint.setTitle(i18n.t("group_paint"))
        self.lbl_paint_mode.setText(i18n.t("lbl_paint_mode"))
        self.radio_sketch.setText(i18n.t("radio_draw_sketch"))
        self.radio_text.setText(i18n.t("radio_write_text"))
        self.lbl_speed.setText(i18n.t("lbl_speed"))
        self.lbl_draw_button.setText(i18n.t("lbl_draw_button"))
        self.btn_settings.setText(i18n.t("btn_settings_open"))
        self.btn_draw_left.setText(i18n.t("draw_button_left"))
        self.btn_draw_right.setText(i18n.t("draw_button_right"))
        self.btn_start_paint.setText(i18n.t("btn_start_paint"))
        self.btn_stop_paint.setText(i18n.t("btn_stop_paint"))
        self._load_draw_button_setting()

    # ──────────── 模式切换 ────────────

    def _on_mode_changed(self, button):
        mode_id = self.mode_group.id(button)
        if mode_id == 0:
            self._paint_mode = "sketch"
            self.text_panel.setVisible(False)
        else:
            self._paint_mode = "text"
            self.text_panel.setVisible(True)

    def _load_draw_button_setting(self):
        draw_button = self._get_paint_settings().get("draw_button")
        self._apply_draw_button(draw_button)

    def _apply_draw_button(self, draw_button: str):
        if draw_button not in {"left", "right"}:
            draw_button = DEFAULT_DRAW_BUTTON_SIDE
        is_left = draw_button == "left"
        self.btn_draw_left.setChecked(is_left)
        self.btn_draw_right.setChecked(not is_left)

    def _on_draw_button_changed(self, draw_button: str):
        self._apply_draw_button(draw_button)
        self._save_paint_settings(draw_button)

    def _current_draw_button(self) -> str:
        assert self.btn_draw_left.isChecked() or self.btn_draw_right.isChecked(), "Draw button toggle must keep one option selected"
        return "left" if self.btn_draw_left.isChecked() else DEFAULT_DRAW_BUTTON_SIDE

    def _refresh_hotkeys(self):
        """根据设置文件中的快捷键配置更新快捷方式。"""
        hotkeys = self._get_hotkey_settings()
        start_seq = QKeySequence(hotkeys.get("start", "F5"))

        if self._start_shortcut:
            try:
                self._start_shortcut.activated.disconnect()
            except Exception:
                pass
            self._start_shortcut.setKey(QKeySequence())
            self._start_shortcut.deleteLater()
            self._start_shortcut = None

        if not start_seq.isEmpty():
            self._start_shortcut = QShortcut(start_seq, self)
            self._start_shortcut.activated.connect(self._on_start_painting)

    def _get_hotkey_settings(self) -> dict:
        """从 settings.json 读取快捷键配置。"""
        defaults = {
            "start": "F5",
            "calib_start": "F7",
            "calib_end": "F8",
            "abort": "Esc",
        }
        if not os.path.isfile(SETTINGS_PATH):
            return defaults
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                settings = json.load(f)
            hotkeys = settings.get("hotkeys", {})
            for key in defaults:
                if key in hotkeys and hotkeys[key]:
                    defaults[key] = hotkeys[key]
        except (json.JSONDecodeError, IOError, KeyError):
            pass
        return defaults

    def _hotkey_value_from_settings(self, key: str, fallback: str) -> str:
        """从设置中获取热键值（小写，供 keyboard 库使用）。"""
        hotkeys = self._get_hotkey_settings()
        val = hotkeys.get(key, fallback)
        return val.replace(" ", "").lower() if val else fallback

    def _get_ai_settings(self) -> dict:
        """从 settings.json 读取 AI 配置。"""
        defaults = {
            "provider": "openai",
            "api_url": "",
            "api_key": "",
            "prompt": "",
        }
        if not os.path.isfile(SETTINGS_PATH):
            return defaults
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                settings = json.load(f)
            ai = settings.get("ai", {})
            for key in defaults:
                if key in ai:
                    defaults[key] = ai[key]
        except (json.JSONDecodeError, IOError, KeyError):
            pass
        return defaults

    def _get_paint_settings(self) -> dict:
        """从 settings.json 读取绘画相关配置。"""
        settings = load_settings()
        paint = settings.get("paint", {})
        draw_button = paint.get("draw_button", DEFAULT_DRAW_BUTTON_SIDE)
        if draw_button not in {"left", "right"}:
            draw_button = DEFAULT_DRAW_BUTTON_SIDE
        return {"draw_button": draw_button}

    def _save_paint_settings(self, draw_button: str):
        """写入绘画相关配置。"""
        settings = load_settings()
        paint = settings.get("paint", {})
        paint["draw_button"] = draw_button
        settings["paint"] = paint
        save_settings(settings)

    def _load_hotkey_settings(self):
        """从 settings.json 加载快捷键并刷新快捷方式。"""
        self._refresh_hotkeys()

    def _on_text_rendered(self, path: str):
        """写字模式下，文字渲染完成后当作线稿数据"""
        self._sketch_data = path
        self.btn_start_paint.setEnabled(True)
        self._pending_history_entry = (
            path,
            "",
            i18n.t("radio_write_text"),
            {
                "text": self.text_panel.text_edit.toPlainText().strip(),
                "font": self.text_panel.font_combo.currentData(),
                "font_size": int(self.text_panel.combo_font_size.currentText()),
            },
        )
        self.sketch_generated.emit(path)
        self.status_message.emit(i18n.t("status_generate_done"))

    def load_sketch_from_history(self, entry: dict, auto_start: bool = False):
        """从历史记录加载线稿并还原界面参数。"""
        path = entry.get("sketch_path", "")
        if not path or not os.path.exists(path):
            return
        self._sketch_data = path
        self.btn_save.setEnabled(True)
        self.btn_start_paint.setEnabled(True)

        # 还原原始图片
        source_path = entry.get("source_path", "")
        if source_path and os.path.isfile(source_path):
            self._image_path = source_path
            filename = os.path.basename(source_path)
            self.lbl_filename.setText(f"📄 {filename}")
            pixmap = QPixmap(source_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.lbl_thumbnail.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.lbl_thumbnail.setPixmap(scaled)
            self.btn_generate.setEnabled(True)
            self.image_selected.emit(source_path)

        # 还原线稿风格
        style = entry.get("style", "")
        if style:
            for idx_s, (key, i18n_key) in enumerate(self.STYLE_KEYS):
                translated = i18n.t(i18n_key)
                if style == translated or style == key:
                    self.combo_style.setCurrentIndex(idx_s)
                    break

        # 还原参数
        params = entry.get("params", {})
        if "thickness" in params:
            self.slider_thickness.setValue(int(params["thickness"]))
        if "contrast" in params:
            self.slider_contrast.setValue(int(params["contrast"]))
        if "threshold" in params:
            self.slider_threshold.setValue(int(params["threshold"]))
        if "invert" in params:
            self.chk_invert.setChecked(bool(params["invert"]))

        self.sketch_generated.emit(path)
        self.status_message.emit(i18n.t("history_restored"))
        if auto_start:
            self._on_start_painting()

    # ──────────── 参数变化防抖 ────────────

    def _on_param_changed(self, _=None):
        self._debounce_timer.start(10)

    # ──────────── 槽函数 ────────────

    def _on_style_changed(self, index):
        pass  # AI 设置已移至设置对话框

    def _on_select_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, i18n.t("dialog_open_title"), "",
            i18n.t("dialog_open_filter")
        )
        if path:
            self._image_path = path
            filename = path.split("/")[-1].split("\\")[-1]
            self.lbl_filename.setText(f"📄 {filename}")

            pixmap = QPixmap(path)
            scaled = pixmap.scaled(
                self.lbl_thumbnail.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.lbl_thumbnail.setPixmap(scaled)

            self.btn_generate.setEnabled(True)
            self.image_selected.emit(path)
            self.status_message.emit(i18n.t("status_image_loaded", filename))
            self.lbl_thumbnail.hide()
            
    def _get_params(self):
        return {
            "thickness": self.slider_thickness.value(),
            "contrast": self.slider_contrast.value(),
            "threshold": self.slider_threshold.value(),
            "invert": self.chk_invert.isChecked(),
        }

    def _on_generate(self):
        if not self._image_path:
            return

        if self._sketch_worker is not None and self._sketch_worker.isRunning():
            try:
                self._sketch_worker.finished.disconnect()
                self._sketch_worker.error.disconnect()
            except RuntimeError:
                pass
            self._sketch_worker.wait()

        style_key = self.combo_style.currentData()
        params = self._get_params()

        self.btn_generate.setEnabled(False)
        self.btn_generate.setText(i18n.t("btn_generating"))
        self.status_message.emit(i18n.t("status_generating"))

        if style_key == "ai":
            ai_settings = self._get_ai_settings()
            self._sketch_worker = AISketchWorker(self._image_path, ai_settings)
        else:
            self._sketch_worker = SketchWorker(self._image_path, style_key, params)
        self._sketch_worker.finished.connect(
            lambda result: self._on_sketch_done(result, style_key, params)
        )
        self._sketch_worker.error.connect(self._on_sketch_error)
        self._sketch_worker.start()

    def _on_sketch_done(self, result, style_key, params):
        self._sketch_data = result
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText(i18n.t("btn_generate"))
        self.btn_save.setEnabled(True)
        self.btn_start_paint.setEnabled(True)
        self.sketch_generated.emit(result)
        self.status_message.emit(i18n.t("status_generate_done"))

        # 暂存历史记录信息，绘画成功后才写入历史
        style_display = i18n.t(f"style_{style_key}") if i18n.t(f"style_{style_key}") != f"style_{style_key}" else style_key
        source = self._image_path or ""
        if isinstance(result, str):
            self._pending_history_entry = (result, source, style_display, params)
        else:
            # result 非字符串路径（如 AI 模式返回图像数组）时不记录历史
            self._pending_history_entry = None

    def _on_sketch_error(self, error_msg):
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText(i18n.t("btn_generate"))
        self.status_message.emit(i18n.t("status_generate_fail", error_msg))

    def _on_save_sketch(self):
        if not self._sketch_data:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, i18n.t("dialog_save_title"), "sketch.png",
            i18n.t("dialog_save_filter")
        )
        if path:
            # TODO: 调用你的保存接口
            # from core.sketch_generator import save_sketch
            # save_sketch(self._sketch_data, path)
            self.status_message.emit(i18n.t("status_saved", path))

    def _on_start_painting(self):
        if not self._sketch_data:
            return
        if self._paint_worker and self._paint_worker.isRunning():
            return
    

        paint_params = {
            "speed": self.slider_speed.value(),
            "draw_button": self._current_draw_button(),
            "mode": self._paint_mode,
            "calibrate_start_key": self._hotkey_value_from_settings("calib_start", "f7"),
            "calibrate_end_key": self._hotkey_value_from_settings("calib_end", "f8"),
            "abort_key": self._hotkey_value_from_settings("abort", "esc"),
        }

        self.btn_start_paint.setEnabled(False)
        self.btn_stop_paint.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_message.emit(i18n.t("status_painting_prepare"))

        self._paint_worker = PaintWorker(self._sketch_data, paint_params)
        self._paint_worker.progress.connect(self._on_paint_progress)
        self._paint_worker.status.connect(self._on_paint_status)
        self._paint_worker.finished.connect(self._on_paint_finished)
        self._paint_worker.error.connect(self._on_paint_error)
        self._paint_worker.start()

    def _on_paint_progress(self, value):
        self.progress_bar.setValue(value)
        self.painting_progress.emit(value)

    def _on_paint_finished(self):
        self.btn_start_paint.setEnabled(True)
        self.btn_stop_paint.setEnabled(False)
        self.status_message.emit(i18n.t("status_painting_done"))

        # 绘画成功后保存到历史记录
        if self._pending_history_entry is not None:
            sketch_path, source_path, style, params = self._pending_history_entry
            self.history_entry.emit(sketch_path, source_path, style, params)
            self._pending_history_entry = None

    def _on_paint_error(self, error_msg):
        self.btn_start_paint.setEnabled(True)
        self.btn_stop_paint.setEnabled(False)
        if error_msg == CANCELLED_SENTINEL:
            self.status_message.emit(i18n.t("status_painting_stopped"))
        else:
            self.status_message.emit(i18n.t("status_painting_error", error_msg))

    def _on_stop_painting(self):
        if self._paint_worker:
            self._paint_worker.stop()
            self.btn_start_paint.setEnabled(True)
            self.btn_stop_paint.setEnabled(False)
            self.status_message.emit(i18n.t("status_painting_stopped"))

    def _on_paint_status(self, message: str):
        self.status_message.emit(message)
        self.notification_message.emit(message)
