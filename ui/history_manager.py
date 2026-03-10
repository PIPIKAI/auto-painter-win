"""
历史记录管理器
自动保存生成的线稿，提供浏览/加载/删除功能
"""
import os
import json
import shutil
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QScrollArea, QFrame, QMenu, QAction,
    QFileDialog, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QCursor

from ui.i18n import i18n
from ui.app_paths import HISTORY_DIR


HISTORY_INDEX = os.path.join(HISTORY_DIR, "index.json")


def _ensure_history_dir():
    os.makedirs(HISTORY_DIR, exist_ok=True)


def _load_index() -> list:
    if os.path.exists(HISTORY_INDEX):
        try:
            with open(HISTORY_INDEX, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_index(entries: list):
    _ensure_history_dir()
    with open(HISTORY_INDEX, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


class HistoryCard(QFrame):
    """单条历史记录卡片"""

    clicked = pyqtSignal(dict)           # 单击
    double_clicked = pyqtSignal(dict)     # 双击加载
    request_delete = pyqtSignal(dict)     # 请求删除
    request_export = pyqtSignal(dict)     # 请求导出
    request_paint = pyqtSignal(dict)      # 请求直接绘画

    THUMB_SIZE = QSize(120, 90)

    def __init__(self, entry: dict, parent=None):
        super().__init__(parent)
        self.entry = entry
        self.setFixedSize(130, 140)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            HistoryCard {
                border: 1px solid #ddd;
                border-radius: 6px;
                background: #fff;
                padding: 4px;
            }
            HistoryCard:hover {
                border-color: #4a90d9;
                background: #f0f7ff;
            }
        """)
        self._selected = False
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # 缩略图
        self.lbl_thumb = QLabel()
        self.lbl_thumb.setFixedSize(self.THUMB_SIZE)
        self.lbl_thumb.setAlignment(Qt.AlignCenter)
        self.lbl_thumb.setStyleSheet("border: none; background: #f8f8f8; border-radius: 4px;")

        thumb_path = self.entry.get("thumbnail", self.entry.get("sketch_path", ""))
        if os.path.exists(thumb_path):
            pixmap = QPixmap(thumb_path).scaled(
                self.THUMB_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.lbl_thumb.setPixmap(pixmap)
        else:
            self.lbl_thumb.setText("?")

        layout.addWidget(self.lbl_thumb, alignment=Qt.AlignCenter)

        # 风格标签
        style_name = self.entry.get("style", "")
        lbl_style = QLabel(style_name)
        lbl_style.setAlignment(Qt.AlignCenter)
        lbl_style.setStyleSheet("font-size: 11px; font-weight: bold; border: none;")
        layout.addWidget(lbl_style)

        # 时间标签
        time_str = self.entry.get("time", "")
        if time_str:
            try:
                dt = datetime.fromisoformat(time_str)
                time_str = dt.strftime("%m-%d %H:%M")
            except ValueError:
                pass
        lbl_time = QLabel(time_str)
        lbl_time.setAlignment(Qt.AlignCenter)
        lbl_time.setStyleSheet("font-size: 10px; color: #999; border: none;")
        layout.addWidget(lbl_time)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.entry)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.entry)
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        act_load = menu.addAction(i18n.t("history_menu_load"))
        act_paint = menu.addAction(i18n.t("history_menu_paint"))
        menu.addSeparator()
        act_export = menu.addAction(i18n.t("history_menu_export"))
        menu.addSeparator()
        act_delete = menu.addAction(i18n.t("history_menu_delete"))
        act_delete.setStyleSheet("color: #d73a49;")

        action = menu.exec_(QCursor.pos())
        if action == act_load:
            self.double_clicked.emit(self.entry)
        elif action == act_paint:
            self.request_paint.emit(self.entry)
        elif action == act_export:
            self.request_export.emit(self.entry)
        elif action == act_delete:
            self.request_delete.emit(self.entry)


class HistoryPanel(QWidget):
    """历史记录面板 - 横向滚动展示"""

    sketch_loaded = pyqtSignal(dict)       # 加载完整历史条目
    sketch_paint = pyqtSignal(str)         # 直接绘画
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries = []
        self._init_ui()
        self._load_history()
        i18n.language_changed.connect(self._retranslate)

    def _init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(4)

        # 标题���
        header = QHBoxLayout()
        self.lbl_title = QLabel()
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 13px;")
        header.addWidget(self.lbl_title)
        header.addStretch()

        self.lbl_clear = QLabel(f"<a href='#'>{i18n.t('history_menu_clear')}</a>")
        self.lbl_clear.setCursor(Qt.PointingHandCursor)
        self.lbl_clear.setStyleSheet("font-size: 11px;")
        self.lbl_clear.linkActivated.connect(self._on_clear_all)
        header.addWidget(self.lbl_clear)

        outer_layout.addLayout(header)

        # 滚动区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedHeight(170)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea { border: 1px solid #ddd; border-radius: 6px; background: #fafafa; }
            QScrollBar:horizontal { height: 8px; background: transparent; }
            QScrollBar::handle:horizontal { background: #ccc; border-radius: 4px; min-width: 30px; }
            QScrollBar::handle:horizontal:hover { background: #aaa; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
        """)

        self.cards_container = QWidget()
        self.cards_layout = QHBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(8, 8, 8, 8)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setAlignment(Qt.AlignLeft)

        # 空状态提示
        self.lbl_empty = QLabel()
        self.lbl_empty.setAlignment(Qt.AlignCenter)
        self.lbl_empty.setStyleSheet("color: #aaa; font-size: 13px;")

        self.scroll.setWidget(self.cards_container)
        outer_layout.addWidget(self.scroll)

        self._retranslate()

    def _retranslate(self, _lang=None):
        self.lbl_title.setText(i18n.t("group_history"))
        self.lbl_clear.setText(f"<a href='#'>{i18n.t('history_menu_clear')}</a>")
        self.lbl_empty.setText(i18n.t("history_empty"))

    def _load_history(self):
        self._entries = _load_index()
        self._rebuild_cards()

    def _rebuild_cards(self):
        # 清除旧卡片
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not self._entries:
            self.cards_layout.addWidget(self.lbl_empty)
            self.lbl_empty.show()
            return

        self.lbl_empty.hide()

        # 按时间倒序（最新在左边）
        for entry in reversed(self._entries):
            card = HistoryCard(entry)
            card.double_clicked.connect(self._on_load)
            card.request_delete.connect(self._on_delete)
            card.request_export.connect(self._on_export)
            card.request_paint.connect(self._on_paint)
            self.cards_layout.addWidget(card)

        # 右侧弹性空间
        self.cards_layout.addStretch()

    def add_entry(self, sketch_path: str, source_path: str, style: str, params: dict):
        """
        新增一条历史记录。
        sketch_path: 线稿图片路径
        source_path: 原始图片路径
        style: 风格名称
        params: 生成参数
        """
        _ensure_history_dir()

        timestamp = datetime.now().isoformat()
        safe_name = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 复制线稿到 history 目录
        ext = os.path.splitext(sketch_path)[1] or ".png"
        saved_name = f"sketch_{safe_name}{ext}"
        saved_path = os.path.join(HISTORY_DIR, saved_name)

        if os.path.exists(sketch_path) and sketch_path != saved_path:
            shutil.copy2(sketch_path, saved_path)
        else:
            saved_path = sketch_path

        # 复制原始图片到 history 目录
        saved_source = ""
        if source_path and os.path.isfile(source_path):
            src_ext = os.path.splitext(source_path)[1] or ".png"
            src_name = f"source_{safe_name}{src_ext}"
            saved_source = os.path.join(HISTORY_DIR, src_name)
            if source_path != saved_source:
                shutil.copy2(source_path, saved_source)

        # 生成缩略图
        thumb_name = f"thumb_{safe_name}.png"
        thumb_path = os.path.join(HISTORY_DIR, thumb_name)
        pixmap = QPixmap(saved_path)
        if not pixmap.isNull():
            thumb = pixmap.scaled(QSize(120, 90), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            thumb.save(thumb_path, "PNG")
        else:
            thumb_path = saved_path

        entry = {
            "sketch_path": saved_path,
            "source_path": saved_source,
            "thumbnail": thumb_path,
            "style": style,
            "params": params,
            "time": timestamp,
        }

        self._entries.append(entry)
        _save_index(self._entries)
        self._rebuild_cards()

    def _on_load(self, entry: dict):
        path = entry.get("sketch_path", "")
        if os.path.exists(path):
            self.sketch_loaded.emit(entry)
            self.status_message.emit(i18n.t("history_loaded"))

    def _on_paint(self, entry: dict):
        path = entry.get("sketch_path", "")
        if os.path.exists(path):
            self.sketch_paint.emit(path)

    def _on_export(self, entry: dict):
        src = entry.get("sketch_path", "")
        if not os.path.exists(src):
            return
        ext = os.path.splitext(src)[1] or ".png"
        path, _ = QFileDialog.getSaveFileName(
            self, i18n.t("dialog_save_title"), f"sketch{ext}",
            i18n.t("dialog_save_filter")
        )
        if path:
            shutil.copy2(src, path)
            self.status_message.emit(i18n.t("history_exported", path))

    def _on_delete(self, entry: dict):
        # 删除文件（线稿、缩略图、原始图片副本）
        for key in ("sketch_path", "thumbnail", "source_path"):
            p = entry.get(key, "")
            if p and os.path.exists(p) and HISTORY_DIR in p:
                try:
                    os.remove(p)
                except OSError:
                    pass

        if entry in self._entries:
            self._entries.remove(entry)
        _save_index(self._entries)
        self._rebuild_cards()
        self.status_message.emit(i18n.t("history_deleted"))

    def _on_clear_all(self):
        reply = QMessageBox.question(
            self, "", i18n.t("history_menu_clear") + "?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # 删除所有文件
            for entry in self._entries:
                for key in ("sketch_path", "thumbnail", "source_path"):
                    p = entry.get(key, "")
                    if p and os.path.exists(p) and HISTORY_DIR in p:
                        try:
                            os.remove(p)
                        except OSError:
                            pass
            self._entries.clear()
            _save_index(self._entries)
            self._rebuild_cards()
            self.status_message.emit(i18n.t("history_cleared"))