"""
主窗口
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QSplitter, QAction, QActionGroup, QMessageBox
)
from PyQt5.QtCore import Qt

from ui.control_panel import ControlPanel
from ui.preview_panel import PreviewPanel
from ui.styles import GLOBAL_STYLE
from ui.i18n import i18n


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.setStyleSheet(GLOBAL_STYLE)

        self._init_menubar()
        self._init_ui()
        self._init_statusbar()

        # 监听语言变化
        i18n.language_changed.connect(self._retranslate)
        self._retranslate()

    # ──────────── 菜单栏 ────────────

    def _init_menubar(self):
        menubar = self.menuBar()

        # 文件菜单
        self.file_menu = menubar.addMenu("")
        self.open_action = QAction("", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self._on_open_image)
        self.file_menu.addAction(self.open_action)

        self.save_action = QAction("", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self._on_save_sketch)
        self.file_menu.addAction(self.save_action)

        self.file_menu.addSeparator()

        self.exit_action = QAction("", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

        # 语言菜单
        self.lang_menu = menubar.addMenu("")
        self.lang_group = QActionGroup(self)
        self.lang_group.setExclusive(True)

        self.action_zh = QAction("", self, checkable=True)
        self.action_zh.setChecked(True)
        self.action_zh.triggered.connect(lambda: i18n.set_language("zh_CN"))
        self.lang_group.addAction(self.action_zh)
        self.lang_menu.addAction(self.action_zh)

        self.action_en = QAction("", self, checkable=True)
        self.action_en.triggered.connect(lambda: i18n.set_language("en_US"))
        self.lang_group.addAction(self.action_en)
        self.lang_menu.addAction(self.action_en)

        # 帮助菜单
        self.help_menu = menubar.addMenu("")
        self.about_action = QAction("", self)
        self.about_action.triggered.connect(self._on_about)
        self.help_menu.addAction(self.about_action)

    # ──────────── UI 布局 ────────────

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Horizontal)

        self.control_panel = ControlPanel()
        self.control_panel.setFixedWidth(300)
        splitter.addWidget(self.control_panel)

        self.preview_panel = PreviewPanel()
        splitter.addWidget(self.preview_panel)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        self._connect_signals()

    def _connect_signals(self):
        self.control_panel.image_selected.connect(self.preview_panel.set_original_image)
        self.control_panel.sketch_generated.connect(self.preview_panel.set_sketch_image)
        self.control_panel.painting_progress.connect(self._update_progress)
        self.control_panel.status_message.connect(self._update_status)

    def _init_statusbar(self):
        self.statusBar()

    # ──────────── 翻译刷新 ────────────

    def _retranslate(self, _lang=None):
        self.setWindowTitle(i18n.t("app_title"))

        # 菜单
        self.file_menu.setTitle(i18n.t("menu_file"))
        self.open_action.setText(i18n.t("menu_open"))
        self.save_action.setText(i18n.t("menu_save"))
        self.exit_action.setText(i18n.t("menu_exit"))

        self.lang_menu.setTitle(i18n.t("menu_language"))
        self.action_zh.setText(i18n.t("lang_zh"))
        self.action_en.setText(i18n.t("lang_en"))

        self.help_menu.setTitle(i18n.t("menu_help"))
        self.about_action.setText(i18n.t("menu_about"))

        # 状态栏
        self.statusBar().showMessage(i18n.t("status_ready"))

    # ──────────── 事件处理 ────────────

    def _update_progress(self, value):
        self.statusBar().showMessage(i18n.t("status_painting_progress", value))

    def _update_status(self, message):
        self.statusBar().showMessage(message)

    def _on_open_image(self):
        self.control_panel._on_select_image()

    def _on_save_sketch(self):
        self.control_panel._on_save_sketch()

    def _on_about(self):
        QMessageBox.about(self, i18n.t("about_title"), i18n.t("about_content"))