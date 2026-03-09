"""
写字模式面板
输入文字 → 渲染为路径图 → 供自动绘画使用
"""
import os
import tempfile

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QSpinBox, QPushButton,
    QGroupBox, QTextEdit, QFontComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QImage, QPainter, QFont, QColor, QPen, QPainterPath

from ui.i18n import i18n



    
class TextPanel(QWidget):
    
    
    """
    写字设置面板。
    将用户输入的文字渲染为黑白路径图，供绘画模块使用。
    """

    text_rendered = pyqtSignal(str)    # 渲染后的图片路径
    status_message = pyqtSignal(str)

    
    # 类变量：(实际字体名, i18n key)
    FONT_LIST = [
        ("SimSun",           "font_simsun"),
        ("SimHei",           "font_simhei"),
        ("Microsoft YaHei",  "font_msyh"),
        ("KaiTi",            "font_kaiti"),
        ("FangSong",         "font_fangsong"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rendered_path = None
        self._init_ui()
        i18n.language_changed.connect(self._retranslate)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.grp_text = QGroupBox()
        grp_layout = QVBoxLayout()

        # 文字输入
        self.lbl_input = QLabel()
        grp_layout.addWidget(self.lbl_input)

        self.text_edit = QTextEdit()
        self.text_edit.setFixedHeight(80)
        self.text_edit.setStyleSheet(
            "border: 1px solid #ccc; border-radius: 4px; padding: 4px; font-size: 14px;"
        )
        grp_layout.addWidget(self.text_edit)

        # 字体选择
        font_row = QHBoxLayout()
        self.lbl_font = QLabel()
        font_row.addWidget(self.lbl_font)
        self.font_combo = QComboBox()
        # 用 addItem(显示名, 实际字体名) 的方式存储
        for font_name, i18n_key in self.FONT_LIST:
            self.font_combo.addItem(i18n.t(i18n_key), font_name)
        font_row.addWidget(self.font_combo, 1)
        grp_layout.addLayout(font_row)

        # 字号
        size_row = QHBoxLayout()
        self.lbl_font_size = QLabel()
        size_row.addWidget(self.lbl_font_size)
        self.combo_font_size = QComboBox()
        self.combo_font_size.addItems([
            "12", "16", "20", "24", "28", "32", "36",
            "48", "56", "64", "72", "96", "128", "160", "200", "256",
        ])
        self.combo_font_size.setCurrentText("72")
        self.combo_font_size.setEditable(False)
        size_row.addWidget(self.combo_font_size)
        size_row.addStretch()
        grp_layout.addLayout(size_row)

        # 预览按钮
        self.btn_preview = QPushButton()
        self.btn_preview.setObjectName("primaryButton")
        self.btn_preview.clicked.connect(self._on_preview)
        grp_layout.addWidget(self.btn_preview)

        self.grp_text.setLayout(grp_layout)
        layout.addWidget(self.grp_text)

        self._retranslate()

    def _retranslate(self, _lang=None):
        self.grp_text.setTitle(i18n.t("group_text"))
        self.lbl_input.setText(i18n.t("lbl_text_input"))
        self.text_edit.setPlaceholderText(i18n.t("placeholder_text"))
        self.lbl_font.setText(i18n.t("lbl_font"))
        self.lbl_font_size.setText(i18n.t("lbl_font_size"))
        self.btn_preview.setText(i18n.t("btn_preview_text"))
        
        # 刷新字体下拉（保持选中项）
        current_idx = self.font_combo.currentIndex()
        self.font_combo.blockSignals(True)
        self.font_combo.clear()
        for font_name, i18n_key in self.FONT_LIST:
            self.font_combo.addItem(i18n.t(i18n_key), font_name)
        self.font_combo.setCurrentIndex(max(0, current_idx))
        self.font_combo.blockSignals(False)
        

    def _on_preview(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            self.status_message.emit(i18n.t("status_text_empty"))
            return

        rendered_path = self._render_text(text)
        if rendered_path:
            self._rendered_path = rendered_path

            self.text_rendered.emit(rendered_path)
            self.status_message.emit(i18n.t("status_text_rendered"))

    def _render_text(self, text: str) -> str:
        """
        将文字渲染为黑底白字（或白底黑字）的路径图。
        返回临时文件路径。
        """
        font = QFont(self.font_combo.currentData())  # 取的是实际字体名，不是显示名
        font.setPixelSize(int(self.combo_font_size.currentText()))

        # 用 QPainterPath 计算文字边界
        path = QPainterPath()
        path.addText(0, 0, font, text)
        bounding = path.boundingRect()

        # 加边距
        margin = 20
        width = int(bounding.width()) + margin * 2
        height = int(bounding.height()) + margin * 2

        # 最小尺寸保护
        width = max(width, 100)
        height = max(height, 50)

        # 创建白底黑字图像
        image = QImage(width, height, QImage.Format_RGB32)
        image.fill(QColor(255, 255, 255))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        # 平移使文字居中
        offset_x = margin - bounding.left()
        offset_y = margin - bounding.top()

        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setBrush(QColor(0, 0, 0))

        translated_path = QPainterPath()
        translated_path.addText(offset_x, offset_y, font, text)
        painter.drawPath(translated_path)

        painter.end()

        # 保存到临时文件
        tmp_dir = tempfile.mkdtemp(prefix="autopainter_text_")
        tmp_path = os.path.join(tmp_dir, "text_render.png")
        image.save(tmp_path, "PNG")

        return tmp_path

    def get_rendered_path(self) -> str:
        return self._rendered_path