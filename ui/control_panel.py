"""
左侧控制面板 - 包含所有操作按钮和参数调整
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QSlider, QComboBox,
    QFileDialog, QSpinBox, QCheckBox, QProgressBar,
    QScrollArea, QFrame, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QPixmap

from ui.i18n import i18n
from core.sketch_generator import SketchGenerator
from core.auto_painter import AutoPainter, PainterConfig, PaintCancelled
from ui.text_panel import TextPanel


CANCELLED_SENTINEL = "__cancelled__"


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


class PaintWorker(QThread):
    """自动绘画工作线程"""
    progress = pyqtSignal(int)
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
            self._painter.start(progress_callback=self.progress.emit)
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

    # 新增：通知主窗口保存历史
    history_entry = pyqtSignal(str, str, str, dict)  # sketch_path, source_path, style, params

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

        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._on_generate)

        self._init_ui()
        i18n.language_changed.connect(self._retranslate)

    def _init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

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

        self.ai_options = QWidget()
        ai_layout = QVBoxLayout(self.ai_options)
        ai_layout.setContentsMargins(0, 4, 0, 0)
        self.lbl_api = QLabel()
        self.lbl_api.setStyleSheet("font-size: 12px;")
        ai_layout.addWidget(self.lbl_api)
        self.combo_api = QComboBox()
        ai_layout.addWidget(self.combo_api)
        self.ai_options.setVisible(False)
        style_layout.addWidget(self.ai_options)

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

        # 起笔延迟
        self.lbl_delay = QLabel()
        paint_layout.addWidget(self.lbl_delay)
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(1, 30)
        self.spin_delay.setValue(5)
        paint_layout.addWidget(self.spin_delay)

        # 画布缩放
        self.lbl_scale = QLabel()
        paint_layout.addWidget(self.lbl_scale)
        self.slider_scale = QSlider(Qt.Horizontal)
        self.slider_scale.setRange(10, 200)
        self.slider_scale.setValue(100)
        self.lbl_scale_val = QLabel("100%")
        h5 = QHBoxLayout()
        h5.addWidget(self.slider_scale)
        h5.addWidget(self.lbl_scale_val)
        paint_layout.addLayout(h5)
        self.slider_scale.valueChanged.connect(
            lambda v: self.lbl_scale_val.setText(f"{v}%")
        )

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

        self.lbl_api.setText(i18n.t("lbl_api"))
        self.combo_api.clear()
        self.combo_api.addItems([
            i18n.t("api_dalle"), i18n.t("api_sd"), i18n.t("api_custom")
        ])

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
        self.lbl_delay.setText(i18n.t("lbl_delay"))
        self.spin_delay.setSuffix(i18n.t("suffix_seconds"))
        self.lbl_scale.setText(i18n.t("lbl_scale"))
        self.btn_start_paint.setText(i18n.t("btn_start_paint"))
        self.btn_stop_paint.setText(i18n.t("btn_stop_paint"))

    # ──────────── 模式切换 ────────────

    def _on_mode_changed(self, button):
        mode_id = self.mode_group.id(button)
        if mode_id == 0:
            self._paint_mode = "sketch"
            self.text_panel.setVisible(False)
        else:
            self._paint_mode = "text"
            self.text_panel.setVisible(True)

    def _on_text_rendered(self, path: str):
        """写字模式下，文字渲染完成后当作线稿数据"""
        self._sketch_data = path
        self.btn_start_paint.setEnabled(True)
        self.sketch_generated.emit(path)

    # ──────────── 参数变化防抖 ────────────

    def _on_param_changed(self, _=None):
        self._debounce_timer.start(10)

    # ──────────── 槽函数 ────────────

    def _on_style_changed(self, index):
        style_key = self.combo_style.currentData()
        self.ai_options.setVisible(style_key == "ai")

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

        # 通知保存到历史记录
        style_display = i18n.t(f"style_{style_key}") if i18n.t(f"style_{style_key}") != f"style_{style_key}" else style_key
        source = self._image_path or ""
        if isinstance(result, str):
            self.history_entry.emit(result, source, style_display, params)

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
    

        paint_params = {
            "speed": self.slider_speed.value(),
            "delay": self.spin_delay.value(),
            "scale": self.slider_scale.value() / 100.0,
            "mode": self._paint_mode,
        }

        self.btn_start_paint.setEnabled(False)
        self.btn_stop_paint.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_message.emit(
            i18n.t("status_painting_countdown", paint_params["delay"])
        )

        self._paint_worker = PaintWorker(self._sketch_data, paint_params)
        self._paint_worker.progress.connect(self._on_paint_progress)
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
