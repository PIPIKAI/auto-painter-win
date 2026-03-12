"""
首次启动/更新提示对话框
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame,
)
from PyQt5.QtCore import Qt, QTimer

from ui.i18n import i18n

# 当 NOTICE_VERSION 变更时，即便用户此前确认过，也会再次提示
NOTICE_VERSION = "2026-03-12"

_DIALOG_STYLE = """
QDialog {
    background-color: #ffffff;
}
QLabel#welcomeTitle {
    font-size: 22px;
    font-weight: bold;
    color: #333333;
}
QLabel#welcomeContent {
    font-size: 14px;
    color: #444444;
    line-height: 1.6;
}
QLabel#welcomeHint {
    font-size: 13px;
    color: #888888;
    padding-top: 4px;
}
QFrame#separator {
    background-color: #e0e0e0;
    max-height: 1px;
}
QPushButton#confirmBtn {
    background-color: #4a90d9;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: bold;
    padding: 10px 32px;
}
QPushButton#confirmBtn:hover {
    background-color: #357abd;
}
QPushButton#confirmBtn:disabled {
    background-color: #a0c4e8;
    color: #e0e0e0;
}
"""


class FirstLaunchDialog(QDialog):
    """首次启动时显示的免责声明与使用提示。"""

    COUNTDOWN_SECONDS = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumWidth(540)
        self.setStyleSheet(_DIALOG_STYLE)

        # 隐藏关闭按钮，仅保留标题栏
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint
        )

        self._seconds_left = self.COUNTDOWN_SECONDS

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(32, 28, 32, 24)

        # 标题行带图标
        self.lbl_title = QLabel()
        self.lbl_title.setObjectName("welcomeTitle")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_title)

        # 分隔线
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.HLine)
        layout.addWidget(sep)

        layout.addSpacing(4)

        # 内容
        self.lbl_content = QLabel()
        self.lbl_content.setObjectName("welcomeContent")
        self.lbl_content.setWordWrap(True)
        self.lbl_content.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.lbl_content.setOpenExternalLinks(True)
        layout.addWidget(self.lbl_content)

        # 提示
        self.lbl_hint = QLabel()
        self.lbl_hint.setObjectName("welcomeHint")
        self.lbl_hint.setWordWrap(True)
        self.lbl_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_hint)

        layout.addSpacing(8)

        # 确认按钮居中
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_confirm = QPushButton()
        self.btn_confirm.setObjectName("confirmBtn")
        self.btn_confirm.setEnabled(False)
        self.btn_confirm.clicked.connect(self.accept)
        btn_row.addWidget(self.btn_confirm)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._update_confirm_text()

        i18n.language_changed.connect(self._retranslate)
        self._retranslate()

    def _tick(self):
        self._seconds_left -= 1
        if self._seconds_left <= 0:
            self._timer.stop()
            self.btn_confirm.setEnabled(True)
        self._update_confirm_text()

    def _retranslate(self, _lang=None):
        self.setWindowTitle(i18n.t("welcome_title"))
        self.lbl_title.setText("🎨 " + i18n.t("welcome_title"))
        self.lbl_content.setText(i18n.t("welcome_message"))
        self.lbl_hint.setText(i18n.t("welcome_hint"))

        self._update_confirm_text()

    def _update_confirm_text(self):
        if self.btn_confirm.isEnabled():
            self.btn_confirm.setText(i18n.t("welcome_confirm"))
        else:
            self.btn_confirm.setText(i18n.t("welcome_confirm_countdown", self._seconds_left))
