"""
主窗口
"""
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QAction, QActionGroup, QMessageBox, QSystemTrayIcon, QStyle
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from ui.control_panel import ControlPanel
from ui.preview_panel import PreviewPanel
from ui.history_manager import HistoryPanel
from ui.settings_dialog import SettingsDialog
from ui.styles import GLOBAL_STYLE
from ui.i18n import i18n


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.setStyleSheet(GLOBAL_STYLE)
        self._tray_icon = None
        self._last_paint_progress = 0
        self._tray_progress_marks_shown = set()

        self._init_menubar()
        self._init_ui()
        self._init_statusbar()
        self._init_tray()

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

        # 设置菜单项（添加到文件菜单分隔符之前）
        self.settings_action = QAction("", self)
        self.settings_action.setShortcut("Ctrl+,")
        self.settings_action.triggered.connect(self._on_open_settings)
        self.file_menu.insertAction(self.exit_action, self.settings_action)
        self.file_menu.insertSeparator(self.exit_action)

    # ──────────── UI 布局 ────────────

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Horizontal)

        self.control_panel = ControlPanel()
        self.control_panel.setFixedWidth(320)
        splitter.addWidget(self.control_panel)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self.preview_panel = PreviewPanel()
        right_layout.addWidget(self.preview_panel, 1)

        self.history_panel = HistoryPanel()
        right_layout.addWidget(self.history_panel, 0)

        splitter.addWidget(right_container)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        self._connect_signals()

    def _connect_signals(self):
        self.control_panel.image_selected.connect(self.preview_panel.set_original_image)
        self.control_panel.sketch_generated.connect(self.preview_panel.set_sketch_image)
        self.control_panel.painting_progress.connect(self._update_progress)
        self.control_panel.status_message.connect(self._update_status)
        self.control_panel.notification_message.connect(self._show_tray_message)
        self.control_panel.history_entry.connect(self.history_panel.add_entry)
        self.control_panel.settings_requested.connect(self._on_open_settings)

        self.history_panel.sketch_loaded.connect(self._on_history_loaded)
        self.history_panel.sketch_paint.connect(self._on_history_paint)
        self.history_panel.status_message.connect(self._update_status)

    def _init_statusbar(self):
        self.statusBar()

    def _init_tray(self):
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "LOGO.ico")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
        else:
            icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        self.setWindowIcon(icon)

        if QSystemTrayIcon.isSystemTrayAvailable():
            self._tray_icon = QSystemTrayIcon(icon, self)
            self._tray_icon.setToolTip(i18n.t("app_title"))
            self._tray_icon.setVisible(True)

    # ──────────── 翻译刷新 ────────────

    def _retranslate(self, _lang=None):
        self.setWindowTitle(i18n.t("app_title"))

        # 菜单
        self.file_menu.setTitle(i18n.t("menu_file"))
        self.open_action.setText(i18n.t("menu_open"))
        self.save_action.setText(i18n.t("menu_save"))
        self.settings_action.setText(i18n.t("menu_settings"))
        self.exit_action.setText(i18n.t("menu_exit"))

        self.lang_menu.setTitle(i18n.t("menu_language"))
        self.action_zh.setText(i18n.t("lang_zh"))
        self.action_en.setText(i18n.t("lang_en"))

        self.help_menu.setTitle(i18n.t("menu_help"))
        self.about_action.setText(i18n.t("menu_about"))

        # 状态栏
        self.statusBar().showMessage(i18n.t("status_ready"))

        if self._tray_icon:
            self._tray_icon.setToolTip(i18n.t("app_title"))

    # ──────────── 事件处理 ────────────

    def _update_progress(self, value):
        self.statusBar().showMessage(i18n.t("status_painting_progress", value))
        self._show_tray_progress(value)

    def _show_tray_progress(self, value: int):
        if not self._tray_icon or not QSystemTrayIcon.isSystemTrayAvailable():
            return
        if value < self._last_paint_progress:
            self._tray_progress_marks_shown.clear()
        self._last_paint_progress = value
        milestone = next((mark for mark in (25, 50, 75) if value >= mark and mark not in self._tray_progress_marks_shown), None)
        if milestone is None:
            return
        self._tray_progress_marks_shown.add(milestone)
        self._tray_icon.showMessage(
            self.windowTitle(),
            i18n.t("status_painting_progress", milestone),
            QSystemTrayIcon.Information,
            20
        )

    def _update_status(self, message):
        self.statusBar().showMessage(message)

    def _show_tray_message(self,title: str, message: str,msec: int ):
        if not self._tray_icon or not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self._tray_icon.showMessage(
            title,
            message,
            QSystemTrayIcon.Information,
            msec
        )

    def _on_history_loaded(self, entry: dict):
        self.control_panel.load_sketch_from_history(entry)

    def _on_history_paint(self, path: str):
        self.control_panel.load_sketch_from_history({"sketch_path": path}, auto_start=True)

    def _on_open_image(self):
        self.control_panel._on_select_image()

    def _on_save_sketch(self):
        self.control_panel._on_save_sketch()

    def _on_about(self):
        QMessageBox.about(self, i18n.t("about_title"), i18n.t("about_content"))

    def _on_open_settings(self):
        dlg = SettingsDialog(self)
        dlg.settings_saved.connect(self._on_settings_saved)
        dlg.exec_()

    def _on_settings_saved(self):
        """设置保存后刷新控制面板的热键。"""
        self.control_panel._refresh_hotkeys()
        self.statusBar().showMessage(i18n.t("settings_saved"))
