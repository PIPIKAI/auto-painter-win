"""
右侧预览面板 - 显示原始图片和线稿对比
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QSizePolicy, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from ui.i18n import i18n


class ImageViewer(QLabel):
    """可缩放的图片查看器"""

    def __init__(self, placeholder_key=""):
        super().__init__()
        self._placeholder_key = placeholder_key
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(200, 200)
        self.setStyleSheet(
            "border: 1px solid #ddd; border-radius: 6px; background: #f8f8f8;"
        )
        self._pixmap = None
        if placeholder_key:
            self.setText(i18n.t(placeholder_key))

    def set_image(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self._update_display()

    def set_image_from_path(self, path: str):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.set_image(pixmap)

    def retranslate(self):
        if self._pixmap is None and self._placeholder_key:
            self.setText(i18n.t(self._placeholder_key))

    def _update_display(self):
        if self._pixmap:
            scaled = self._pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_display()


class PreviewPanel(QWidget):
    """预览面板"""

    def __init__(self):
        super().__init__()
        self._init_ui()
        i18n.language_changed.connect(self._retranslate)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()

        # ── Tab 1: 对比视图 ──
        compare_widget = QWidget()
        compare_layout = QHBoxLayout(compare_widget)
        compare_layout.setSpacing(8)

        left_container = QVBoxLayout()
        self.lbl_orig_title = QLabel()
        self.lbl_orig_title.setAlignment(Qt.AlignCenter)
        self.lbl_orig_title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 4px;")
        left_container.addWidget(self.lbl_orig_title)

        self.viewer_original = ImageViewer("placeholder_select")
        left_container.addWidget(self.viewer_original)
        compare_layout.addLayout(left_container)

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("color: #ddd;")
        compare_layout.addWidget(separator)

        right_container = QVBoxLayout()
        self.lbl_sketch_title = QLabel()
        self.lbl_sketch_title.setAlignment(Qt.AlignCenter)
        self.lbl_sketch_title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 4px;")
        right_container.addWidget(self.lbl_sketch_title)

        self.viewer_sketch = ImageViewer("placeholder_sketch")
        right_container.addWidget(self.viewer_sketch)
        compare_layout.addLayout(right_container)

        # 设置左侧布局的伸缩因子，使左侧和右侧的比例固定
        compare_layout.setStretch(0, 1)  # 左侧部分
        compare_layout.setStretch(2, 1)  # 右侧部分不伸缩
        self.tabs.addTab(compare_widget, "")

        # ── Tab 2: 仅原图 ──
        orig_only = QWidget()
        orig_only_layout = QVBoxLayout(orig_only)
        self.viewer_original_full = ImageViewer("placeholder_select")
        orig_only_layout.addWidget(self.viewer_original_full)
        self.tabs.addTab(orig_only, "")

        # ── Tab 3: 仅线稿 ──
        sketch_only = QWidget()
        sketch_only_layout = QVBoxLayout(sketch_only)
        self.viewer_sketch_full = ImageViewer("placeholder_sketch")
        sketch_only_layout.addWidget(self.viewer_sketch_full)
        self.tabs.addTab(sketch_only, "")

        layout.addWidget(self.tabs)

        # 初始翻译
        self._retranslate()

    def _retranslate(self, _lang=None):
        self.lbl_orig_title.setText(i18n.t("lbl_original_title"))
        self.lbl_sketch_title.setText(i18n.t("lbl_sketch_title"))
        self.tabs.setTabText(0, i18n.t("tab_compare"))
        self.tabs.setTabText(1, i18n.t("tab_original"))
        self.tabs.setTabText(2, i18n.t("tab_sketch"))

        # 刷新占位文字
        self.viewer_original.retranslate()
        self.viewer_sketch.retranslate()
        self.viewer_original_full.retranslate()
        self.viewer_sketch_full.retranslate()

    def set_original_image(self, path: str):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.viewer_original.set_image(pixmap)
            self.viewer_original_full.set_image(pixmap)

    def set_sketch_image(self, data):
        if isinstance(data, str):
            pixmap = QPixmap(data)
            if not pixmap.isNull():
                self.viewer_sketch.set_image(pixmap)
                self.viewer_sketch_full.set_image(pixmap)
        else:
            # TODO: numpy array → QPixmap
            pass